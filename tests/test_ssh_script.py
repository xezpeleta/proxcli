"""Tests for the `auth setup` bash script generator (proxmox.ssh.script)."""

from __future__ import annotations

import subprocess

import pytest

from proxmox.cli.auth import GUEST_EXEC_PRIV, PROXCLI_ACLS, PROXCLI_ROLES, _build_roles
from proxmox.ssh.script import SetupSpec, generate_manual_commands, generate_setup_script


def _spec(**kw) -> SetupSpec:
    base = dict(
        pve_user="root@pam",
        token_name="proxcli",
        roles=dict(PROXCLI_ROLES),
        acls=list(PROXCLI_ACLS),
    )
    base.update(kw)
    return SetupSpec(**base)


class TestScriptGeneration:
    def test_basic_structure(self):
        """The script has the expected header, sections, and DONE sentinel."""
        script = generate_setup_script(_spec())
        assert script.startswith("#!/usr/bin/env bash")
        assert "set -uo pipefail" in script
        assert "role_ensure" in script
        assert "acl_ensure" in script
        assert 'ok "DONE"' in script

    def test_contains_every_role(self):
        """A role_ensure call is emitted for each role in the spec."""
        script = generate_setup_script(_spec())
        for name in PROXCLI_ROLES:
            assert f"role_ensure '{name}'" in script

    def test_contains_every_acl(self):
        """An acl_ensure call is emitted for each (path, role) pair."""
        script = generate_setup_script(_spec())
        for path, role in PROXCLI_ACLS:
            assert f"acl_ensure '{path}' '{role}'" in script

    def test_privsep_flag(self):
        """privsep=True -> PRIVSEP='1', privsep=False -> PRIVSEP='0'."""
        assert "PRIVSEP='1'" in generate_setup_script(_spec(privsep=True))
        assert "PRIVSEP='0'" in generate_setup_script(_spec(privsep=False))

    def test_regenerate_flag(self):
        """regenerate toggles the REGENERATE var and the branch taken."""
        on = generate_setup_script(_spec(regenerate=True))
        off = generate_setup_script(_spec(regenerate=False))
        assert "REGENERATE='1'" in on
        assert "REGENERATE='0'" in off
        # The regenerate branch calls pvesh set --regenerate
        assert "--regenerate 1" in on

    def test_user_and_token_interpolated(self):
        """pve_user and token_name appear in the generated UG variable."""
        script = generate_setup_script(_spec(pve_user="admin@pve", token_name="ci"))
        assert "PVE_USER='admin@pve'" in script
        assert "TOKEN='ci'" in script

    def test_shell_quoting_special_chars(self):
        """A user/token with a single quote is safely escaped."""
        script = generate_setup_script(_spec(pve_user="o'reilly@pam"))
        # The safe idiom for an embedded single quote
        assert "'o'\"'\"'reilly@pam'" in script

    def test_bash_syntax_valid(self):
        """The generated script passes `bash -n` (syntax check)."""
        script = generate_setup_script(_spec())
        proc = subprocess.run(
            ["bash", "-n"], input=script, capture_output=True, text=True
        )
        assert proc.returncode == 0, f"bash -n failed:\n{proc.stderr}"

    @pytest.mark.parametrize("missing", ["pve_user", "token_name"])
    def test_missing_required_raises(self, missing):
        """Missing pve_user or token_name is rejected."""
        kw = dict(pve_user="root@pam", token_name="proxcli", roles={"r": "p"}, acls=[])
        kw[missing] = ""
        with pytest.raises(ValueError, match="required"):
            generate_setup_script(SetupSpec(**kw))

    def test_empty_roles_raises(self):
        """An empty roles mapping is rejected."""
        with pytest.raises(ValueError, match="at least one role"):
            generate_setup_script(
                SetupSpec(pve_user="root@pam", token_name="t", roles={}, acls=[])
            )

    def test_secret_extractor_present(self):
        """The _extract_secret helper (python3 + grep fallback) is included."""
        script = generate_setup_script(_spec())
        assert "_extract_secret()" in script
        assert "json.load" in script
        assert "grep" in script  # fallback path

    def test_token_creation_uses_pvesh_json(self):
        """Token creation uses pvesh create with --output-format json."""
        script = generate_setup_script(_spec())
        assert 'pvesh create "$TOKEN_PATH" --privsep "$PRIVSEP" --output-format json' in script
        assert 'pvesh get "$TOKEN_PATH"' in script  # existence check


class TestGuestExecRole:
    """The --allow-guest-exec flag adds VM.GuestAgent.Unrestricted to proxcli-vm."""

    def test_default_omits_guest_exec(self):
        """Without the flag, proxcli-vm has no VM.GuestAgent.Unrestricted."""
        roles = _build_roles(allow_guest_exec=False)
        privs = roles["proxcli-vm"].split(",")
        assert GUEST_EXEC_PRIV not in privs
        # the read-only guest-agent privs are still present
        assert "VM.GuestAgent.Audit" in privs
        assert "VM.GuestAgent.FileRead" in privs

    def test_flag_adds_guest_exec(self):
        """With the flag, proxcli-vm gains VM.GuestAgent.Unrestricted."""
        roles = _build_roles(allow_guest_exec=True)
        privs = roles["proxcli-vm"].split(",")
        assert GUEST_EXEC_PRIV in privs
        assert "VM.GuestAgent.Audit" in privs  # read-only privs preserved

    def test_flag_only_touches_proxcli_vm(self):
        """The flag does not alter any other role."""
        off = _build_roles(allow_guest_exec=False)
        on = _build_roles(allow_guest_exec=True)
        for name in off:
            if name == "proxcli-vm":
                continue
            assert off[name] == on[name]

    def test_flag_propagates_into_script(self):
        """The generated bash script includes the privilege when the flag is on."""
        script = generate_setup_script(_spec(roles=_build_roles(allow_guest_exec=True)))
        # role_ensure 'proxcli-vm' '...VM.GuestAgent.Unrestricted'
        assert "role_ensure 'proxcli-vm'" in script
        assert GUEST_EXEC_PRIV in script
        # and is absent when the flag is off
        script_off = generate_setup_script(_spec(roles=_build_roles(allow_guest_exec=False)))
        assert GUEST_EXEC_PRIV not in script_off


class TestManualCommandGeneration:
    """Tests for generate_manual_commands — the flat pveum/pvesh command list."""

    def test_produces_flat_pveum_pvesh_commands(self):
        out = generate_manual_commands(_spec())
        # No bash-script scaffolding — these are commands to paste, not a script.
        assert "#!/usr/bin/env bash" not in out
        assert "set -uo pipefail" not in out
        assert "role_ensure()" not in out
        # The actual pveum/pvesh invocations are present.
        assert "pveum role add" in out
        assert "pvesh create" in out
        assert "pveum acl modify" in out

    def test_roles_are_idempotent_add_or_modify(self):
        """Each role line falls back from `add` to `modify` so re-runs are safe."""
        out = generate_manual_commands(_spec())
        assert "pveum role add 'proxcli-sys'" in out
        assert "|| pveum role modify 'proxcli-sys'" in out

    def test_token_create_command_uses_privsep(self):
        out = generate_manual_commands(_spec(privsep=True))
        assert "pvesh create '/access/users/root@pam/token/proxcli' --privsep 1" in out
        out_no = generate_manual_commands(_spec(privsep=False))
        assert "--privsep 0" in out_no

    def test_regenerate_uses_pvesh_set(self):
        out = generate_manual_commands(_spec(regenerate=True))
        assert "pvesh set" in out
        assert "--regenerate 1" in out
        assert "pvesh create" not in out

    def test_acls_reference_token_ugid(self):
        out = generate_manual_commands(_spec())
        assert "--tokens 'root@pam!proxcli'" in out
        # ACL command shape: pveum acl modify '<path>' --tokens '<ug>' --roles '<role>'
        assert "pveum acl modify '/' --tokens 'root@pam!proxcli' --roles 'proxcli-sys'" in out

    def test_custom_user_token_quoted(self):
        out = generate_manual_commands(_spec(pve_user="admin@pve", token_name="ci"))
        assert "/access/users/admin@pve/token/ci" in out
        assert "--tokens 'admin@pve!ci'" in out

    def test_guest_exec_flag_propagates(self):
        out = generate_manual_commands(_spec(roles=_build_roles(allow_guest_exec=True)))
        assert GUEST_EXEC_PRIV in out
        out_off = generate_manual_commands(_spec(roles=_build_roles(allow_guest_exec=False)))
        assert GUEST_EXEC_PRIV not in out_off

    def test_quotes_single_quotes_in_user(self):
        out = generate_manual_commands(_spec(pve_user="o'reilly@pam"))
        # The _sh idiom escapes an embedded single quote as the 5-char sequence '"'"'.
        bash_quote_escape = "'\"'\"'"
        assert bash_quote_escape in out


class TestBackupsReadOnlyByDefault:
    """The default roles must NOT grant backup-modifying privileges.

    On PVE, deleting a backup volume requires ``Datastore.Allocate`` (or the
    combination ``Datastore.AllocateSpace`` + ``VM.Backup`` on the owning VM),
    and creating a vzdump backup requires ``VM.Backup``.  Both are intentionally
    absent from the default roles so that a freshly-bootstrapped token can list
    and inspect backups but cannot create or delete them.
    """

    def test_datastore_allocate_absent_from_storage_role(self):
        """Datastore.Allocate is the delete-volume privilege — must be absent."""
        privs = PROXCLI_ROLES["proxcli-storage"].split(",")
        assert "Datastore.Allocate" not in privs
        # The non-destructive storage privs are still present.
        assert "Datastore.AllocateSpace" in privs
        assert "Datastore.AllocateTemplate" in privs
        assert "Datastore.Audit" in privs

    def test_vm_backup_absent_from_vm_role(self):
        """VM.Backup grants vzdump create + is the alt-path for backup delete."""
        privs = PROXCLI_ROLES["proxcli-vm"].split(",")
        assert "VM.Backup" not in privs
        # Core VM lifecycle privs are still present.
        assert "VM.Allocate" in privs
        assert "VM.Snapshot" in privs
        assert "VM.Snapshot.Rollback" in privs

    def test_no_default_role_grants_backup_delete(self):
        """No role in the default set may carry Datastore.Allocate."""
        for name, privs_str in PROXCLI_ROLES.items():
            assert "Datastore.Allocate" not in privs_str.split(","), (
                f"{name} must not grant Datastore.Allocate (backup delete)"
            )

    def test_no_default_role_grants_vm_backup(self):
        """No role in the default set may carry VM.Backup."""
        for name, privs_str in PROXCLI_ROLES.items():
            assert "VM.Backup" not in privs_str.split(","), (
                f"{name} must not grant VM.Backup (backup create/delete)"
            )

    def test_generated_script_omits_backup_privs(self):
        """The manual commands and SSH script must not contain the privs."""
        for out in (generate_manual_commands(_spec()), generate_setup_script(_spec())):
            # Datastore.Allocate must not appear as a standalone priv token.
            # (Datastore.AllocateSpace / AllocateTemplate / AllocateAudit are fine.)
            assert ",Datastore.Allocate," not in out
            assert "Datastore.Allocate " not in out
            # VM.Backup must not appear at all.
            assert "VM.Backup" not in out
