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
        """Initialize the twitter module.

        Opens a connection to:
         * twitter.com via tweepy and
         * the sqlite-database.

        Adds all required tables to the sqlite-database (if not already present).
        Prepares a status processor handling tweets.

        Parameters
        ----------

        user_id : str
            The twitter user's id
        consumer_key : str
            The twitter api's consumer key
        consumer_secret : str
            The twitter api's consumer secret
        access_token : str
            The twitter user's access token
        access_secret : str
            The twitter user's access secret
        db_file : str
            The sqlite database
        """
        self.db = db_file
        self.user_id = user_id
        self.prepare_db()

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(auth)

        self.stream = None

    def listen(self):
        """Start listening on the user's twitter stream

        Starts an async tweepy stream that follows the specified user.
        """
        logging.info("Listening on twitter stream")
        streamProcessor = StreamProcessor()
        streamProcessor.prepare(self.db)
        self.stream = tweepy.Stream(auth = self.api.auth,
            listener= streamProcessor,
            tweet_mode='extended')
        self.stream.filter(follow=[self.user_id], is_async=True)

    def stop(self):
        """Disconnect from the tweepy stream"""
        if self.stream:
            self.stream.disconnect()


    def prepare_db(self):
        """Prepare the database by creating all required tables if they do
        not exist.
        """
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
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
        conn.commit()
        conn.close()

    def get_max_tweet_id(self):
        """Return the id of the latest tweet stored in the database"""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute('SELECT MAX(tweet_id) FROM tweets;')
        result = c.fetchone()
        conn.close()
        if result[0]:
            return result[0]
        return 0


    def archive_later_than(self, min_tweet_id: int):
        """Archive the latest tweets of the user.

        Archives all tweets with tweet_id > 'min_tweet_id'.
        When twitter's api-request-limiter jumps in, the static limit_handled
        function is called.

        Parameters
        ----------

        min_tweet_id : int
            The minimal tweet id
        """
        logging.info("Archiving tweets with id > {}".format(min_tweet_id))
        processor = status_processor.StatusProcessor(self.db)
        for status in limit_handled(tweepy.Cursor(self.api.user_timeline,
            user_id = self.user_id, tweet_mode='extended',
            since_id=min_tweet_id).items()):
            processor.process_status(status)
        processor.close_connection()

    def archive_latest(self, num_tweets: int):
        """Archive the latest tweets of the user.

        Archives the latest 'num_tweets' tweets of the user.
        When twitter's api-request-limiter jumps in, the static limit_handled
        function is called.

        Parameters
        ----------

        num_tweets : int
            The number of latest tweets to archive
        """
        logging.info("Archiving {} tweets".format(num_tweets))
        processor = status_processor.StatusProcessor(self.db)
        for status in limit_handled(tweepy.Cursor(self.api.user_timeline, user_id = self.user_id, tweet_mode='extended').items(num_tweets)):
            processor.process_status(status)
        processor.close_connection()

    def add_status_to_db(self, status_id: int):
        """Add a specific status to the database.

        Parameters
        ----------

        status_id : int
            The id of the status that is to be added to the database
        """
        logging.info("Processing status {}".format(status_id))
        processor = status_processor.StatusProcessor(self.db)
        status = self.api.get_status(status_id, tweet_mode='extended')
        processor.process_status(status)
        processor.close_connection()

def limit_handled(cursor):
    """Handle the twitter api's time limits.

    Example:
    >>> for status in limit_handled(cursor.items(10)):

    Parameters
    ----------

    cursor : tweepy.Cursor
        The cursor hat is to be handled

    Returns
    -------
    tweepy.Status
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
