import os
import subprocess
import logging

class Sftp(object):

    def __init__(self, folder: str, address: str, config_file: str,
            password: str = None):
        self.folder = folder
        self.address = address
        self.config_file = config_file
        self.password = password

    def remote_reset(self):
        pass

    def update(self):
        pass
