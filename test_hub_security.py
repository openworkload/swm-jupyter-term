import unittest

from swmjupyter.hub_security import (
    AUTHENTICATOR_DUMMY,
    AUTHENTICATOR_OAUTH,
    AUTHENTICATOR_NATIVE,
    HubSecurityError,
    bind_url,
    docker_publish_arg,
    resolve_hub_security,
)


class TestResolveHubSecurity(unittest.TestCase):
    def test_default_is_native_loopback(self):
        settings = resolve_hub_security({})
        self.assertEqual(settings.authenticator_class, AUTHENTICATOR_NATIVE)
        self.assertFalse(settings.allow_all)
        self.assertFalse(settings.open_signup)
        self.assertEqual(settings.bind_ip, "127.0.0.1")
        self.assertEqual(settings.bind_port, 8000)
        self.assertEqual(bind_url(settings), "http://127.0.0.1:8000")

    def test_admin_user(self):
        settings = resolve_hub_security({"SWM_JUPYTER_ADMIN_USER": "alice"})
        self.assertEqual(settings.admin_users, frozenset({"alice"}))

    def test_publish_all_sets_all_interfaces(self):
        settings = resolve_hub_security({"SWM_JUPYTER_PUBLISH_ALL": "1"})
        self.assertEqual(settings.bind_ip, "0.0.0.0")
        self.assertEqual(settings.authenticator_class, AUTHENTICATOR_NATIVE)

    def test_dummy_without_insecure_rejected(self):
        with self.assertRaises(HubSecurityError):
            resolve_hub_security({"SWM_JUPYTER_AUTH": "dummy"})

    def test_insecure_dummy_loopback_allowed(self):
        settings = resolve_hub_security(
            {
                "SWM_JUPYTER_INSECURE_AUTH": "1",
                "SWM_JUPYTER_BIND_IP": "127.0.0.1",
            }
        )
        self.assertEqual(settings.authenticator_class, AUTHENTICATOR_DUMMY)
        self.assertTrue(settings.allow_all)
        self.assertTrue(settings.insecure_auth)

    def test_insecure_dummy_all_interfaces_rejected(self):
        with self.assertRaises(HubSecurityError) as ctx:
            resolve_hub_security(
                {
                    "SWM_JUPYTER_AUTH": "dummy",
                    "SWM_JUPYTER_INSECURE_AUTH": "1",
                    "SWM_JUPYTER_BIND_IP": "0.0.0.0",
                }
            )
        self.assertIn("loopback", str(ctx.exception).lower())

    def test_oauth_requires_env(self):
        with self.assertRaises(HubSecurityError) as ctx:
            resolve_hub_security({"SWM_JUPYTER_AUTH": "oauth"})
        self.assertIn("OAUTH2_CLIENT_ID", str(ctx.exception))

    def test_oauth_ok(self):
        settings = resolve_hub_security(
            {
                "SWM_JUPYTER_AUTH": "oauth",
                "OAUTH2_CLIENT_ID": "id",
                "OAUTH2_CLIENT_SECRET": "secret",
                "OAUTH2_AUTHORIZE_URL": "https://idp/authorize",
                "OAUTH2_TOKEN_URL": "https://idp/token",
                "OAUTH2_USERDATA_URL": "https://idp/user",
            }
        )
        self.assertEqual(settings.authenticator_class, AUTHENTICATOR_OAUTH)
        self.assertFalse(settings.allow_all)
        self.assertEqual(settings.oauth_client_id, "id")

    def test_production_non_loopback_requires_tls(self):
        with self.assertRaises(HubSecurityError):
            resolve_hub_security(
                {
                    "SWM_JUPYTER_ENV": "production",
                    "SWM_JUPYTER_BIND_IP": "0.0.0.0",
                }
            )

    def test_production_with_tls_ok(self):
        settings = resolve_hub_security(
            {
                "SWM_JUPYTER_ENV": "production",
                "SWM_JUPYTER_BIND_IP": "0.0.0.0",
                "SWM_JUPYTER_SSL_CERT": "/certs/cert.pem",
                "SWM_JUPYTER_SSL_KEY": "/certs/key.pem",
            }
        )
        self.assertTrue(settings.require_tls)
        self.assertEqual(bind_url(settings), "https://0.0.0.0:8000")

    def test_unknown_auth_rejected(self):
        with self.assertRaises(HubSecurityError):
            resolve_hub_security({"SWM_JUPYTER_AUTH": "ldap"})


class TestDockerPublishArg(unittest.TestCase):
    def test_loopback(self):
        self.assertEqual(docker_publish_arg("127.0.0.1", 8000), "127.0.0.1:8000:8000")

    def test_all_interfaces(self):
        self.assertEqual(docker_publish_arg("0.0.0.0", 8000), "8000:8000")


if __name__ == "__main__":
    unittest.main()
