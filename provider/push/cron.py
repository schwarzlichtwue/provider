import os
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
try:
	from provider.push.git import Git
	import provider.push.processor as processor
	import provider.push.filecreator as filecreator
except ImportError:
	from push.git import Git
	import push.processor as processor
	import push.filecreator as filecreator

class Cron:

	def __init__(self, user_id: int, db_file: str, ssh_file: str, update_interval: int, folder: str):
		self.user_id = user_id
		self.db = db_file
		self.ssh_file = ssh_file
		self.repo_folder = folder
		self.media_folder = os.path.join(folder, 'media')
		scheduler = BackgroundScheduler()
		try:
			update_interval = int(update_interval)
		except ValueError:
			update_interval = 2 # (default)
		scheduler.add_job(self.callback, 'interval', hours=update_interval, replace_existing=True)
		scheduler.start()

	def callback(self):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		c.execute('SELECT tweet_id, text, user_id, created_at, reply_to_status, reply_to_user, quoted_status_id FROM tweets WHERE user_id = ? AND (reply_to_user IS NULL OR reply_to_user = ?);', (self.user_id, self.user_id))
		rows = c.fetchall()
		prepared_rows = []
		for row in rows:
			prepared_rows += [{
			'tweet_id': row[0],
			'text': row[1],
			'user_id': row[2],
			'created_at': row[3],
			'reply_to_status': row[4],
			'reply_to_user': row[5],
			'quoted_status_id': row[6],
			}]
		obj_list = processor.process(self.user_id, conn, prepared_rows)
		conn.close()
		git = Git(self.ssh_file, self.repo_folder)
		git.checkout('dev')
		git.pull()
		for obj in obj_list:
			filecreator.create(os.path.join(self.repo_folder, '_posts'), obj)
			try:
				if obj['media']:
					# TODO
					pass
			except KeyError:
				pass
		git.update()
