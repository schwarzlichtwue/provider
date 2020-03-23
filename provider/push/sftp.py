import os
import subprocess
import logging

class Sftp(object):

    def __init__(self, address: str, local_folder:str,
            remote_folder: str,
            user:          str,
            password:      str = None):
        self.address = address
        self.batch_file = '/tmp/batch_file.txt'
        self.user = user
        self.local_folder = local_folder
        self.remote_folder = remote_folder
        self.password = password

    def update(self):
        logging.info("Mirroring to remote")
        cmd = ['lftp', '-f', """
open {}
user {} '{}'
lcd {}
mirror --exclude .git/ --exclude .gitignore --reverse --only-newer --delete --verbose {} {}
bye
""".format(
    self.address, self.user, self.password, self.local_folder,
    self.local_folder, self.remote_folder)
]
        resp = subprocess.run(cmd)
        if resp.returncode != 0:
            logging.warn("Mirroring to remote failed.")
