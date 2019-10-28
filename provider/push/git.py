import os
import subprocess
import logging

class Git(object):

    def __init__(self, folder: str, ssh_file: str = None):
        self.folder = folder
        self.ssh_file = ssh_file
        self.can_push = ssh_file is not None

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
        if self.can_push:
            logging.info("Pushing in {}".format(self.folder))
            cmd = ['git', '-C', self.folder, 'push']
            subprocess.run(cmd)

    def update(self):
        self.checkout('dev')
        self.pull()

        logging.info("Performing jekyll build of {}".format(self.folder))
        cmd = ['cd {} && jekyll build -d /tmp/_site'.format(self.folder)]
        subprocess.run(cmd, shell=True)

        self.push('new tweets')

        self.checkout('master')
        self.pull()

        cmd = ['cp -r /tmp/_site/* {} && rm -rf /tmp/_site'.format(self.folder)]
        subprocess.run(cmd, shell=True)

        self.push('new tweets')
