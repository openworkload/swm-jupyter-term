c.JupyterHub.spawner_class = 'swmspawner.swmspawner.SwmSpawner'

c.SwmSpawner.swm_host = 'localhost'
c.SwmSpawner.swm_port = 8443
c.SwmSpawner.swm_ca_file = '~/.swm/spool/secure/cluster/ca-chain-cert.pem'
c.SwmSpawner.swm_key_file = '~/.swm/key.pem'
c.SwmSpawner.swm_cert_file = '~/.swm/cert.pem'
c.SwmSpawner.debug_singleuser_daemon = False
