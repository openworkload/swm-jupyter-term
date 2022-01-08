import os
import platform
import sys

# For development purpose we use the spawner package from the sources:
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from swm_jupyter_spawner.spawner import SwmSpawner

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.spawner_class = 'swm_jupyter_spawner.spawner.SwmSpawner'
c.JupyterHub.shutdown_on_logout = False

c.PAMAuthenticator.open_sessions = False

c.SwmSpawner._swm_host = platform.node()
c.SwmSpawner._swm_port = 8443
c.SwmSpawner._swm_ca_file = '~/.swm/spool/secure/cluster/ca-chain-cert.pem'
c.SwmSpawner._swm_key_file = '~/.swm/key.pem'
c.SwmSpawner._swm_cert_file = '~/.swm/cert.pem'
c.SwmSpawner._debug_singleuser_daemon = False
c.SwmSpawner._remote_port = 8888
c.SwmSpawner.options_form = lambda spawner: spawner.render_options_form()
