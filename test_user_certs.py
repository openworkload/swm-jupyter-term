import os
import pwd
import tempfile
import unittest

from swmjupyter.user_certs import UserCertError, resolve_user_cert_paths, sanitize_cert_username


def _fake_pw(name: str, home: str) -> pwd.struct_passwd:
    return pwd.struct_passwd((name, "x", 1001, 1001, "", home, "/bin/bash"))


class TestSanitizeCertUsername(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(sanitize_cert_username("alice"), "alice")
        self.assertEqual(sanitize_cert_username("bob.smith-1"), "bob.smith-1")

    def test_rejects_unsafe(self):
        for bad in ("", "../alice", "a/b", "alice\\x", ".", "..", "alice\x00", "-alice"):
            with self.subTest(bad=bad):
                with self.assertRaises(UserCertError):
                    sanitize_cert_username(bad)


class TestResolveUserCertPaths(unittest.TestCase):
    def test_resolves_system_user_home(self):
        with tempfile.TemporaryDirectory() as home:
            swm = os.path.join(home, ".swm")
            ca_dir = os.path.join(swm, "spool", "secure", "cluster")
            os.makedirs(ca_dir, mode=0o700)
            cert = os.path.join(swm, "cert.pem")
            key = os.path.join(swm, "key.pem")
            ca = os.path.join(ca_dir, "ca-chain-cert.pem")
            for path in (cert, key, ca):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("test")
                os.chmod(path, 0o600)

            def getpwnam(name: str) -> pwd.struct_passwd:
                if name != "alice":
                    raise KeyError(name)
                return _fake_pw("alice", home)

            paths = resolve_user_cert_paths("alice", getpwnam=getpwnam)
            self.assertEqual(paths.cert_file, cert)
            self.assertEqual(paths.key_file, key)
            self.assertEqual(paths.ca_file, ca)
            self.assertEqual(paths.home_dir, home)

    def test_two_users_get_distinct_homes(self):
        with tempfile.TemporaryDirectory() as root:
            homes = {}
            for name in ("alice", "bob"):
                home = os.path.join(root, name)
                swm = os.path.join(home, ".swm")
                ca_dir = os.path.join(swm, "spool", "secure", "cluster")
                os.makedirs(ca_dir, mode=0o700)
                for rel in ("cert.pem", "key.pem", "spool/secure/cluster/ca-chain-cert.pem"):
                    path = os.path.join(home, ".swm", rel)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(name)
                    os.chmod(path, 0o600)
                homes[name] = home

            def getpwnam(name: str) -> pwd.struct_passwd:
                if name not in homes:
                    raise KeyError(name)
                return _fake_pw(name, homes[name])

            alice = resolve_user_cert_paths("alice", getpwnam=getpwnam)
            bob = resolve_user_cert_paths("bob", getpwnam=getpwnam)
            self.assertNotEqual(alice.cert_file, bob.cert_file)
            self.assertTrue(alice.cert_file.startswith(homes["alice"]))
            self.assertTrue(bob.cert_file.startswith(homes["bob"]))

    def test_missing_system_user(self):
        def getpwnam(name: str) -> pwd.struct_passwd:
            raise KeyError(name)

        with self.assertRaises(UserCertError) as ctx:
            resolve_user_cert_paths("nobody", getpwnam=getpwnam)
        self.assertIn("No system user", str(ctx.exception))

    def test_missing_cert_fails(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, ".swm"), mode=0o700)

            def getpwnam(name: str) -> pwd.struct_passwd:
                return _fake_pw(name, home)

            with self.assertRaises(UserCertError) as ctx:
                resolve_user_cert_paths("alice", getpwnam=getpwnam)
            self.assertIn("not found", str(ctx.exception).lower())

    def test_ca_override(self):
        with tempfile.TemporaryDirectory() as home:
            swm = os.path.join(home, ".swm")
            os.makedirs(swm, mode=0o700)
            cert = os.path.join(swm, "cert.pem")
            key = os.path.join(swm, "key.pem")
            shared_ca = os.path.join(home, "shared-ca.pem")
            for path in (cert, key, shared_ca):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("x")
                os.chmod(path, 0o644)

            paths = resolve_user_cert_paths(
                "alice",
                ca_file=shared_ca,
                getpwnam=lambda n: _fake_pw(n, home),
            )
            self.assertEqual(paths.ca_file, shared_ca)

    def test_unreadable_key_fails(self):
        with tempfile.TemporaryDirectory() as home:
            swm = os.path.join(home, ".swm")
            ca_dir = os.path.join(swm, "spool", "secure", "cluster")
            os.makedirs(ca_dir, mode=0o700)
            cert = os.path.join(swm, "cert.pem")
            key = os.path.join(swm, "key.pem")
            ca = os.path.join(ca_dir, "ca-chain-cert.pem")
            for path in (cert, key, ca):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("x")
            os.chmod(key, 0o000)

            try:
                with self.assertRaises(UserCertError) as ctx:
                    resolve_user_cert_paths(
                        "alice",
                        getpwnam=lambda n: _fake_pw(n, home),
                    )
                self.assertIn("not readable", str(ctx.exception).lower())
            finally:
                os.chmod(key, 0o600)


if __name__ == "__main__":
    unittest.main()
