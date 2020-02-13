import os
import subprocess
import logging

class Git(object):

    def __init__(self, folder: str):
        self.folder = folder

    def checkout(self, branch: str):
        logging.info("Checking out branch {}".format(branch))
        cmd = ['git', '-C', self.folder, 'checkout', branch]
        subprocess.run(cmd)

    def pull(self):
        logging.info("Pulling in {}".format(self.folder))
        cmd = ['git', '-C', self.folder, 'pull']
        subprocess.run(cmd)

    def push(self, message: str):
        logging.info("Adding all files in {}".format(self.folder))
        cmd = ['git', '-C', self.folder, 'add', '*']
        subprocess.run(cmd)
        logging.info("Committing in {} with message '{}'".format(self.folder, message))
        cmd = ['git', '-C', self.folder, 'commit', '-m', message]
        subprocess.run(cmd)
        logging.info("Pushing in {}".format(self.folder))
        cmd = ['git', '-C', self.folder, 'push']
        subprocess.run(cmd)
