import os
import subprocess
import logging

class Sftp(object):

    def __init__(self, address: str, local_folder:str,
            remote_folder: str,
            config_file:   str,
            password:      str = None):
        self.address = address
        self.batch_file = '/tmp/batch_file.txt'
        self.config_file = config_file
        self.local_folder = local_folder
        self.remote_folder = remote_folder
        self.password = password

    def update(self, new: list = [], modified: list = [], removed: list = []):
        logging.info("Syncing to remote")
        with open(self.batch_file, 'w') as batch:
            for line in new + modified:
                local_path = os.path.join(self.local_folder, line)
                target_path = os.path.join(self.remote_folder, line)
                entry = 'put {} {}\n'.format(local_path, target_path)
                batch.write(entry)
            for line in removed:
                target_path = os.path.join(self.remote_folder, line)
                entry = 'rm {}\n'.format(target_path)
                batch.write(entry)
            if len(new + modified + removed) == 0: # full push if no modification
                entry = 'put -r {}/* {}\n'.format(self.local_folder,
                        self.remote_folder)
                batch.write(entry)
            batch.write('exit\n')
        cmd = ['sshpass', '-p', self.password, 'sftp', '-r', '-oBatchMode=no', '-F', self.config_file,
                '-b', self.batch_file, self.address]
        resp = subprocess.run(cmd)
        if resp.returncode != 0: # It was not possible to sync. Full push
            logging.warn("Not possible to sync. Pushing complete folder")
            with open(self.batch_file, 'w') as batch:
                entry = 'put -r {}/* {}\nexit\n'.format(self.local_folder,
                        self.remote_folder)
                batch.write(entry)
            cmd = ['sshpass', '-p', self.password, 'sftp', '-oBatchMode=no', '-F', self.config_file,
                    '-b', self.batch_file, self.address]
            subprocess.run(cmd)
