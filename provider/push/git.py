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

    def get_diff(self):
        cmd = ['git', '-C', self.folder,
                'diff', '--name-status', 'HEAD^', 'HEAD']
        resp = subprocess.run(cmd, capture_output=True)
        text_response = resp.stdout.decode()
        new      = []
        modified = []
        removed  = []
        for line in text_response.split('\n'):
            split_line = line.split('\t')
            if len(split_line) < 2:
                continue
            if split_line[0] == 'D':
                removed  += [split_line[1]]
            elif split_line[0] == 'M':
                modified += [split_line[1]]
            else:
                new      += [split_line[1]]
        return new, modified, removed
