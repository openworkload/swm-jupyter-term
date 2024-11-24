import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from swmjupyter.spawner import SwmSpawner

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.spawner_class = 'swmjupyter.spawner.SwmSpawner'

c.JupyterHub.authenticator_class = 'dummy'
c.JupyterHub.oauth_token_expires_in = 3600
c.JupyterHub.tornado_settings = {"slow_spawn_timeout": 0}
c.Authenticator.allow_all = True

c.SwmSpawner._swm_ca_file = '~/.swm/spool/secure/cluster/ca-chain-cert.pem'
c.SwmSpawner._swm_key_file = '~/.swm/key.pem'
c.SwmSpawner._swm_cert_file = '~/.swm/cert.pem'
c.SwmSpawner.start_timeout = 1800
c.SwmSpawner.http_timeout = 60
c.SwmSpawner.debug = True
