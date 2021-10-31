import os
#from tempfile import TemporaryDirectory

from traitlets import Bool
from traitlets import Unicode
from traitlets import Integer
from traitlets import observe
from jupyterhub.spawner import Spawner


class SwmSpawner(Spawner):

    _swm_port = Integer(8443, help='SWM port number', config=True)
    _swm_host = Unicode('localhost', help='SWM hostname', config=True)
    _swm_ca_file = Unicode('~/.swm/spool/secure/cluster/ca-chain-cert.pem', help='CA file path', config=True)
    _swm_key_file = Unicode('~/.swm/key.pem', help='PEM key file path', config=True)
    _swm_cert_file = Unicode('~/.swm/cert.pem', help='PEM certificate file path', config=True)
    _debug_singleuser_daemon = Bool(False, help='Enable debug messages for singleuser server', config=True)

    async def start(self):
        '''Start single-user server over SWM.'''

        username = self.user.name
        ca_file = self._swm_ca_file.format(username=username)
        key_file = self._swm_key_file.format(username=username)
        cert_file = self._swm_cert_file.format(username=username)

        self.job_id = await self._do_submit_rpc(remote_cmd)
        self.log.debug(f'Starting User: {self.user.name}, PID: {self.pid}')

        if not self.job_id:
            return None

        #TODO get ip and port of the remote container where singluser server runs (do we need to save them in state?)
        return remote_ip, remote_port

    async def poll(self):
        '''Poll swm-spawned process to see if it is still running.

        return None if it is still running, otherwise 0.'''

        job_state = self._fetch_job_state()
        if job_state in ['R', 'W', 'T']:  # TODO use enum
            return None
        self.clear_state()
        return 0

    async def stop(self, now=False):
        '''Stop single-user server process for the current user.'''
        alive = await self._do_cancel_rpc()
        self.clear_state()

    def _fetch_job_state(self):
        #TODO
        pass

    @observe('remote_host')
    def _log_remote_host(self, change):
        self.log.debug("Remote host was set to %s." % self.remote_host)

    @observe('remote_ip')
    def _log_remote_ip(self, change):
        self.log.debug("Remote IP was set to %s." % self.remote_ip)

    async def _do_submit_rpc(self, command):
        """Perform RPC call to SWM"""

        # run_script = "/tmp/{}_run.sh".format(self.user.name)
        # with open(run_script, "w") as f:
            # f.write(bash_script_str)
        # if not os.path.isfile(run_script):
            # raise Exception("The file " + run_script + "was not created.")
        # else:
            # with open(run_script, "r") as f:
                # self.log.debug(run_script + " was written as:\n" + f.read())

    async def _do_cancel_rpc(self):
        '''Cancel the singleuser job'''
        # TODO
