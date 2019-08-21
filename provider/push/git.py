import os
import subprocess

class Git(object):

	def __init__(self, ssh_file: str, folder: str):
		self.folder = folder
		self.ssh_file = ssh_file

	def checkout(self, branch: str):
		cmd = ['git', '-C', self.folder, 'checkout', branch]
		subprocess.run(cmd)

	def pull(self):
		cmd = ['git', '-C', self.folder, 'pull']
		subprocess.run(cmd)

	def push(self, message: str):
		cmd = ['git', '-C', self.folder, 'add', '*']
		subprocess.run(cmd)
		cmd = ['git', '-C', self.folder, 'commit', '-m', message]
		subprocess.run(cmd)
		cmd = ['git', '-C', self.folder, 'push']
		subprocess.run(cmd)

	def update(self):
		self.checkout('dev')
		self.pull()

		cmd = ['cd {} && jekyll build -d /tmp/_site'.format(self.folder)]
		subprocess.run(cmd, shell=True)

		self.push('new tweets')

		self.checkout('master')
		self.pull()

		cmd = ['cp -r /tmp/_site/* {} && rm -rf /tmp/_site'.format(self.folder)]
		subprocess.run(cmd, shell=True)

		self.push('new tweets')
