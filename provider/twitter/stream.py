import tweepy
import sqlite3
import logging

try:
    import twitter.status as status_processor
except ImportError:
    import provider.twitter.status as status_processor

class StreamProcessor(tweepy.StreamListener):
    db = None

    def prepare(self, db):
        self.db = db

    def on_status(self, status):
        logging.info("Stream retrieved status")
        processor = status_processor.StatusProcessor(self.db)
        processor.process_status(status)
