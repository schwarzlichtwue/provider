import tweepy
import sqlite3
import logging

try:
	import twitter.status as status_processor
except ImportError:
	import provider.twitter.status as status_processor

class StreamProcessor(tweepy.StreamListener):
	def prepare(self, conn):
		self.conn = conn

	def on_status(self, status):
		logging.info("Stream retrieved status")
		status_processor.process_status(self.conn, status)
