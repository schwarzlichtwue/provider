import os
import subprocess
import logging

class Sftp(object):

    def __init__(self, address: str, batch_file:str,
            config_file: str,
            password: str = None):
        self.address = address
        self.batch_file = batch_file
        self.config_file = config_file
        self.password = password

    def remote_reset(self):
        pass

    def update(self):
        logging.info("Syncing to remote")
        cmd = ['sshpass', '-p', self.password, 'sftp', '-oBatchMode=no', '-F', self.config_file,
                '-b', self.batch_file, self.address]
        subprocess.run(cmd)
