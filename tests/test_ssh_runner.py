"""Tests for the SSH runner and setup-output parser (proxmox.ssh.runner)."""

from __future__ import annotations

import subprocess

import pytest

from proxmox.ssh.runner import SshError, SshResult, SshRunner, parse_setup_output

# ---------------------------------------------------------------------------
# parse_setup_output
# ---------------------------------------------------------------------------


class TestParseSetupOutput:
    def test_token_created_with_secret(self):
        """A successful creation emits TOKEN_CREATED + TOKEN_SECRET + DONE."""
        out = (
            "PROXCLI:ROLE_CREATED:proxcli-sys\n"
            "PROXCLI:TOKEN_CREATED:root@pam!proxcli\n"
            "PROXCLI:TOKEN_SECRET:abc-123-def\n"
            "PROXCLI:ACL_SET:/:proxcli-sys\n"
            "PROXCLI:DONE\n"
        )
        r = parse_setup_output(out)
        assert r.done is True
        assert r.ok is True
        assert r.roles_created == ["proxcli-sys"]
        assert r.token_ug == "root@pam!proxcli"
        assert r.token_status == "created"
        assert r.token_secret == "abc-123-def"
        assert r.acls_set == ["/"]

    def test_secret_with_colons_preserved(self):
        """The secret is everything after TOKEN_SECRET: (colons included)."""
        r = parse_setup_output("PROXCLI:TOKEN_SECRET:a:b:c\n")
        assert r.token_secret == "a:b:c"

    def test_token_exists(self):
        """An existing token without --regenerate reports exists (no secret)."""
        r = parse_setup_output("PROXCLI:TOKEN_EXISTS:root@pam!proxcli\nPROXCLI:DONE\n")
        assert r.token_status == "exists"
        assert r.token_secret is None
        assert r.done is True
        # exists is not a failure
        assert r.ok is True

    def test_token_regenerated(self):
        r = parse_setup_output(
            "PROXCLI:TOKEN_REGENERATED:u@pam!t\nPROXCLI:TOKEN_SECRET:new-secret\nPROXCLI:DONE\n"
        )
        assert r.token_status == "regenerated"
        assert r.token_secret == "new-secret"

    def test_role_and_acl_failures(self):
        """Failures are captured and make .ok False."""
        out = (
            "PROXCLI:ROLE_CREATE_FAILED:proxcli-vm\n"
            "PROXCLI:ACL_FAILED:/sdn:proxcli-network\n"
            "PROXCLI:DONE\n"
        )
        r = parse_setup_output(out)
        assert r.role_failures == ["proxcli-vm"]
        assert r.acl_failures == ["/sdn"]
        assert r.done is True
        assert r.ok is False

    def test_role_updated(self):
        r = parse_setup_output("PROXCLI:ROLE_UPDATED:proxcli-sys\nPROXCLI:DONE\n")
        assert r.roles_updated == ["proxcli-sys"]

    def test_missing_done_means_not_ok(self):
        r = parse_setup_output("PROXCLI:ROLE_CREATED:proxcli-sys\n")
        assert r.done is False
        assert r.ok is False

    def test_noise_lines_ignored(self):
        """Non-PROXCLI lines and blank lines are tolerated."""
        out = "some stderr leakage\n\nPROXCLI:DONE\nrandom\n"
        r = parse_setup_output(out)
        assert r.done is True
        assert r.raw_sentinels == ["PROXCLI:DONE"]

    def test_empty_output(self):
        r = parse_setup_output("")
        assert r.done is False
        assert r.token_secret is None
        assert r.ok is False

    def test_to_dict_shape(self):
        r = parse_setup_output("PROXCLI:TOKEN_CREATED:u!t\nPROXCLI:TOKEN_SECRET:s\nPROXCLI:DONE\n")
        d = r.to_dict()
        assert d["token"] == {"user_token": "u!t", "status": "created", "secret": "s"}
        assert d["ok"] is True
        assert "roles_created" in d and "acls_set" in d


# ---------------------------------------------------------------------------
# SshRunner.build_command
# ---------------------------------------------------------------------------


class TestSshRunnerCommand:
    def test_key_auth_command(self):
        """Key auth: ssh with BatchMode, no sshpass prefix."""
        runner = SshRunner(host="pve1", user="root", port=2222)
        cmd = runner.build_command("bash -s")
        assert cmd[0] == "ssh"
        assert "sshpass" not in cmd
        assert "-o" in cmd and "BatchMode=yes" in cmd
        assert "StrictHostKeyChecking=accept-new" in cmd
        assert "-p" in cmd and "2222" in cmd
        assert "root@pve1" in cmd
        assert cmd[-1] == "bash -s"

    def test_identity_flag(self):
        runner = SshRunner(host="pve1", identity="/home/u/.ssh/id_ed25519")
        cmd = runner.build_command()
        assert "-i" in cmd
        idx = cmd.index("-i")
        assert cmd[idx + 1] == "/home/u/.ssh/id_ed25519"

    def test_password_uses_sshpass(self, monkeypatch):
        """Password auth prepends sshpass -p and requires it to exist."""
        monkeypatch.setattr("proxmox.ssh.runner.shutil.which", lambda _: "/usr/bin/sshpass")
        runner = SshRunner(host="pve1", password="s3cr3t")
        cmd = runner.build_command()
        assert cmd[0] == "sshpass"
        assert cmd[1] == "-p"
        assert cmd[2] == "s3cr3t"
        # ssh follows sshpass
        assert "ssh" in cmd

    def test_password_without_sshpass_raises(self, monkeypatch):
        """Password auth without sshpass installed raises a helpful SshError."""
        monkeypatch.setattr("proxmox.ssh.runner.shutil.which", lambda _: None)
        runner = SshRunner(host="pve1", password="s3cr3t")
        with pytest.raises(SshError, match="sshpass"):
            runner.build_command()

    def test_extra_opts_appended(self):
        runner = SshRunner(host="pve1", extra_opts=["-o", "ServerAliveInterval=30"])
        cmd = runner.build_command()
        assert "ServerAliveInterval=30" in cmd

    def test_empty_host_raises(self):
        with pytest.raises(SshError, match="host is required"):
            SshRunner(host="")


# ---------------------------------------------------------------------------
# SshRunner.run_script
# ---------------------------------------------------------------------------


class TestSshRunnerRunScript:
    def test_dry_run_returns_script_without_executing(self, monkeypatch):
        """dry_run=True returns the script as stdout and never calls ssh."""
        called = {"n": 0}

        def fake_run(*a, **kw):
            called["n"] += 1
            pytest.fail("subprocess.run must not be called in dry-run")

        monkeypatch.setattr("proxmox.ssh.runner.subprocess.run", fake_run)
        runner = SshRunner(host="pve1")
        res = runner.run_script("echo hi\n", dry_run=True)
        assert called["n"] == 0
        assert isinstance(res, SshResult)
        assert res.returncode == 0
        assert res.stdout == "echo hi\n"

    def test_run_script_invokes_subprocess(self, monkeypatch):
        """run_script pipes the script to ssh stdin and returns the result."""

        captured = {}

        class FakeProc:
            returncode = 0
            stdout = "PROXCLI:DONE\n"
            stderr = ""

        def fake_run(cmd, input, capture_output, text, timeout):
            captured["cmd"] = cmd
            captured["input"] = input
            captured["timeout"] = timeout
            return FakeProc()

        monkeypatch.setattr("proxmox.ssh.runner.subprocess.run", fake_run)
        runner = SshRunner(host="pve1")
        res = runner.run_script("the script", timeout=42)
        assert res.returncode == 0
        assert res.stdout == "PROXCLI:DONE\n"
        assert captured["input"] == "the script"
        assert captured["timeout"] == 42
        assert captured["cmd"][-1] == "bash -s"
        assert "root@pve1" in captured["cmd"]

    def test_timeout_raises_ssherror(self, monkeypatch):
        def fake_run(*a, **kw):
            raise subprocess.TimeoutExpired(cmd="ssh", timeout=1)

        monkeypatch.setattr("proxmox.ssh.runner.subprocess.run", fake_run)
        runner = SshRunner(host="pve1")
        with pytest.raises(SshError, match="timed out"):
            runner.run_script("x")

    def test_missing_ssh_binary_raises_ssherror(self, monkeypatch):
        monkeypatch.setattr(
            "proxmox.ssh.runner.subprocess.run",
            lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("ssh")),
        )
        runner = SshRunner(host="pve1")
        with pytest.raises(SshError, match="ssh"):
            runner.run_script("x")
