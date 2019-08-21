import tweepy
import sqlite3

try:
	import twitter.status as status_processor
except ImportError:
	import provider.twitter.status as status_processor

class StreamProcessor(tweepy.StreamListener):
	def prepare(self, db_file: str):
		self.db = db_file

	def on_status(self, status):
		conn = sqlite3.connect(self.db)
		c = conn.cursor()
		status_processor.process_status(c, status)
		conn.commit()
		conn.close()
