"""SSH transport + result parsing for `proxmox auth setup --via ssh`.

The runner shells out to the system ``ssh`` client (respecting ``~/.ssh/config``)
so proxcli needs no Python SSH library.  Password auth is supported only when
``sshpass`` is installed on the workstation; key-based auth is the baseline.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class SshResult:
    """Raw result of an SSH command execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class SetupResult:
    """Parsed outcome of a setup script run, built from `PROXCLI:` sentinels."""

    roles_created: list[str] = field(default_factory=list)
    roles_updated: list[str] = field(default_factory=list)
    role_failures: list[str] = field(default_factory=list)
    token_ug: str | None = None
    token_status: str = "unknown"  # created|exists|regenerated|create_failed|regen_failed
    token_secret: str | None = None
    acls_set: list[str] = field(default_factory=list)
    acl_failures: list[str] = field(default_factory=list)
    done: bool = False
    raw_sentinels: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if the script finished and nothing failed."""
        return self.done and not self.role_failures and not self.acl_failures

    def to_dict(self) -> dict:
        return {
            "roles_created": self.roles_created,
            "roles_updated": self.roles_updated,
            "role_failures": self.role_failures,
            "token": {
                "user_token": self.token_ug,
                "status": self.token_status,
                "secret": self.token_secret,
            },
            "acls_set": self.acls_set,
            "acl_failures": self.acl_failures,
            "ok": self.ok,
        }


# ---------------------------------------------------------------------------
# Output parser (pure, testable)
# ---------------------------------------------------------------------------


def parse_setup_output(stdout: str) -> SetupResult:
    """Parse ``PROXCLI:`` sentinel lines from setup-script stdout.

    Non-sentinel lines are ignored (the script suppresses most command output,
    but stray lines are tolerated).
    """
    res = SetupResult()
    for line in stdout.splitlines():
        line = line.rstrip("\r")
        if not line.startswith("PROXCLI:"):
            continue
        res.raw_sentinels.append(line)
        body = line[len("PROXCLI:"):]
        parts = body.split(":", 2)
        event = parts[0]

        if event == "ROLE_CREATED":
            res.roles_created.append(parts[1] if len(parts) > 1 else "?")
        elif event == "ROLE_UPDATED":
            res.roles_updated.append(parts[1] if len(parts) > 1 else "?")
        elif event in ("ROLE_CREATE_FAILED", "ROLE_UPDATE_FAILED"):
            res.role_failures.append(parts[1] if len(parts) > 1 else "?")
        elif event == "TOKEN_CREATED":
            res.token_ug = parts[1] if len(parts) > 1 else None
            res.token_status = "created"
        elif event == "TOKEN_EXISTS":
            res.token_ug = parts[1] if len(parts) > 1 else None
            res.token_status = "exists"
        elif event == "TOKEN_REGENERATED":
            res.token_ug = parts[1] if len(parts) > 1 else None
            res.token_status = "regenerated"
        elif event == "TOKEN_CREATE_FAILED":
            res.token_ug = parts[1] if len(parts) > 1 else None
            res.token_status = "create_failed"
        elif event == "TOKEN_REGEN_FAILED":
            res.token_ug = parts[1] if len(parts) > 1 else None
            res.token_status = "regen_failed"
        elif event == "TOKEN_SECRET":
            # The secret is everything after "TOKEN_SECRET:" (secrets may
            # theoretically contain colons, so do not split further).
            res.token_secret = body[len("TOKEN_SECRET:"):] if "TOKEN_SECRET:" in body else None
        elif event == "ACL_SET":
            res.acls_set.append(parts[1] if len(parts) > 1 else "?")
        elif event == "ACL_FAILED":
            res.acl_failures.append(parts[1] if len(parts) > 1 else "?")
        elif event == "DONE":
            res.done = True
    return res


# ---------------------------------------------------------------------------
# SSH runner
# ---------------------------------------------------------------------------


class SshError(Exception):
    """Raised when SSH cannot be executed or fails to connect."""


class SshRunner:
    """Run a script on a remote host via the system ``ssh`` client.

    Auth strategy:
      * **Key-based** (default, recommended): ``ssh`` uses ``~/.ssh/config`` and
        the agent/identity files. ``BatchMode=yes`` prevents hanging on a
        password prompt — connection fails fast if the key is not authorized.
      * **Password**: only when ``sshpass`` is installed. The password is passed
        to ``sshpass`` (never on the ssh command line).
    """

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        identity: str | None = None,
        password: str | None = None,
        connect_timeout: int = 15,
        extra_opts: list[str] | None = None,
    ):
        if not host:
            raise SshError("SSH host is required")
        self.host = host
        self.user = user
        self.port = port
        self.identity = identity
        self.password = password
        self.connect_timeout = connect_timeout
        self.extra_opts = list(extra_opts) if extra_opts else []

    # ------------------------------------------------------------------

    def _sshpass_available(self) -> bool:
        return shutil.which("sshpass") is not None

    def build_command(self, remote_cmd: str = "bash -s") -> list[str]:
        """Build the argv for an SSH invocation.

        With ``remote_cmd='bash -s'`` the script is read from stdin (see
        :meth:`run_script`).
        """
        cmd: list[str] = []

        if self.password:
            if not self._sshpass_available():
                raise SshError(
                    "Password auth requires 'sshpass' on your workstation.\n"
                    "  Debian/Ubuntu: sudo apt install sshpass\n"
                    "  Fedora/RHEL:   sudo dnf install sshpass\n"
                    "  macOS (brew):  brew install hudochenkov/sshpass/sshpass\n"
                    "Alternatively, use SSH key-based auth (omit the password)."
                )
            cmd += ["sshpass", "-p", self.password]

        cmd += ["ssh"]
        # Key auth: never hang on a prompt. Password auth: sshpass feeds it.
        cmd += ["-o", "BatchMode=yes"]
        cmd += ["-o", f"ConnectTimeout={self.connect_timeout}"]
        cmd += ["-o", "StrictHostKeyChecking=accept-new"]
        cmd += ["-p", str(self.port)]
        if self.identity:
            cmd += ["-i", self.identity]
        cmd += list(self.extra_opts)
        cmd += [f"{self.user}@{self.host}"]
        cmd += [remote_cmd]
        return cmd

    def run_script(
        self,
        script: str,
        timeout: int = 120,
        dry_run: bool = False,
    ) -> SshResult:
        """Execute ``script`` on the remote host via ``ssh ... bash -s``.

        With ``dry_run=True`` the command is not executed; an :class:`SshResult`
        with the script as stdout is returned (the caller can preview it).
        """
        if dry_run:
            return SshResult(returncode=0, stdout=script, stderr="")

        cmd = self.build_command("bash -s")
        try:
            proc = subprocess.run(
                cmd,
                input=script,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SshError(
                f"SSH command timed out after {timeout}s connecting to "
                f"{self.user}@{self.host}:{self.port}"
            ) from exc
        except FileNotFoundError as exc:
            raise SshError(
                "The 'ssh' client was not found on your PATH. Install OpenSSH."
            ) from exc
        return SshResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)

    def can_connect(self, timeout: int = 20) -> bool:
        """Return True if a trivial remote command succeeds."""
        try:
            res = self.run_script("echo PROXCLI_PING\n", timeout=timeout)
        except SshError:
            return False
        return res.ok and "PROXCLI_PING" in res.stdout
