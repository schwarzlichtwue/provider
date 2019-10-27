import os
import sqlite3
import logging

from apscheduler.schedulers.background import BackgroundScheduler

try:
	from provider.push.git import Git
	from provider.push.refine import Refine
	import provider.push.filecreator as filecreator
except ImportError:
	from push.git import Git
	from push.refine import Refine
	import push.filecreator as filecreator

class Cron:

	def __init__(self, user_id: int, db_file: str, ssh_file: str, update_interval: int, folder: str):
		self.user_id = user_id
		self.db = db_file
		self.ssh_file = ssh_file
		self.folder = folder
		self.scheduler = BackgroundScheduler()
		try:
			update_interval = int(update_interval)
		except ValueError:
			update_interval = 2 # (default)
		logging.info("Starting background update job with interval {}h".format(update_interval))
		self.scheduler.add_job(self.callback, 'interval', hours=update_interval, replace_existing=True)
		self.scheduler.start()

	def stop(self):
		self.scheduler.shutdown()

	def callback(self):
		logging.info("Update started")
		conn = sqlite3.connect(self.db)
		refine = Refine(self.user_id, conn)
		obj_list = refine.refine()
		conn.close()
		git = Git(self.folder, self.ssh_file)
		git.checkout('dev')
		git.pull()
		for obj in obj_list:
			filecreator.create(self.folder, obj)
		git.update()
		logging.info("Update finished")
