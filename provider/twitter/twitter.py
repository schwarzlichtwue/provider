from datetime import datetime
import time
import tweepy
import sqlite3
import logging

try:
    from twitter.stream import StreamProcessor
    import twitter.status as status_processor
except ImportError:
    from provider.twitter.stream import StreamProcessor
    import provider.twitter.status as status_processor

class Twitter:

    def __init__(self, user_id:str, consumer_key: str, consumer_secret:
            str, access_token: str, access_secret: str, db_file: str):
        self.db = db_file
        self.conn = sqlite3.connect(self.db)
        self.user_id = user_id
        self.prepare_db()
        self.processor = status_processor.StatusProcessor(self.db)

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(auth)

        self.stream = None

    def listen(self):
        logging.info("Listening on twitter stream")
        streamProcessor = StreamProcessor()
        streamProcessor.prepare(self.db)
        self.stream = tweepy.Stream(auth = self.api.auth,
            listener= streamProcessor,
            tweet_mode='extended')
        self.stream.filter(follow=[self.user_id], is_async=True)

    def stop(self):
        if self.stream:
            self.stream.disconnect()
        logging.info("Closing connection to database {}".format(self.db))
        self.conn.commit()
        self.conn.close()
        logging.info("Connection to database {} closed".format(self.db))


    def prepare_db(self):
        """
        prepare the database by creating all required tables if they do not exist
        """
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS "tweets" (
"tweet_id" INTEGER UNIQUE,
"text" TEXT,
"user_id" INTEGER,
"created_at" TEXT,
"reply_to_status" INTEGER,
"reply_to_user" INTEGER,
"quoted_status_id" INTEGER,
PRIMARY KEY("tweet_id")
);''')
        c.execute('''CREATE TABLE IF NOT EXISTS "users" (
"user_id" INTEGER UNIQUE,
"name" TEXT,
"screen_name" TEXT,
"image" BLOB,
"created_at" TEXT,
"description" TEXT,
PRIMARY KEY("user_id")
);''')
        c.execute('''CREATE TABLE IF NOT EXISTS "tweet_media" (
"media_id" INTEGER NOT NULL UNIQUE,
"tweet_id" INTEGER,
"is_video" INTEGER,
"data" BLOB
);''')
        c.execute('''CREATE TABLE IF NOT EXISTS "tweet_tags" (
"tag_name" TEXT,
"tweet_id" INTEGER
);''')
        c.execute('''CREATE TABLE IF NOT EXISTS "tweet_urls" (
"display_url" TEXT,
"url" TEXT,
"tweet_id" INTEGER
);''')
        logging.info("Committing CREATE TABLE queries")
        self.conn.commit()

    def archive(self, num_tweets: int):
        """
        Archives past num_tweets tweets of the user
        """
        logging.info("Archiving {} tweets".format(num_tweets))
        for status in limit_handled(tweepy.Cursor(self.api.user_timeline, user_id = self.user_id, tweet_mode='extended').items(num_tweets)):
            self.processor.process_status(status)

    def add_status_to_db(self, status_id: int):
        """
        Adds the status identified by status_id to the database
        """
        logging.info("Processing status {}".format(status_id))
        status = self.api.get_status(status_id, tweet_mode='extended')
        self.processor.process_status(status)

def limit_handled(cursor):
    """
    Function for handling the twitter api time limits
    """
    try:
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                timeout = 15*60
                logging.warning("Reached twitter api rate limit. Waiting {} seconds".format(timeout))
                time.sleep(timeout)
    except StopIteration:
        return
