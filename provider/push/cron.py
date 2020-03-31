import os
import sqlite3
import logging

from apscheduler.schedulers.background import BackgroundScheduler

try:
    from provider.push.git import Git
    from provider.push.jekyll import Jekyll
    from provider.push.refine import Refine
    import provider.push.filecreator as filecreator
except ImportError:
    from push.git import Git
    from push.jekyll import Jekyll
    from push.refine import Refine
    import push.filecreator as filecreator

class Cron:

    def __init__(self, user_id: int, db_file: str,
            update_interval: int, jekyll_source: str, jekyll_target: str,
            sftp, twitter):
        """Start a scheduler which pushes jekyll changes at regular intervals

        Creates a jekyll instance and registers a background (async) scheduler
        to perform jekyll builds and git pushes at regular intervals

        Parameters
        ----------

        user_id : int
            The twitter user's id
        db_file : str
            The sqlite3 database
        update_interval : int
            The update interval (in hours) by which the scheduler is configured
        jekyll_source : str
            The folder where jekyll source files are located at.
            Cron performes pushes for any changes made here
        jekyll_target : str
            The folder where jekyll is built in.
            Cron performes pushes for any changes made here
        sftp : str
            A sftp object
        twitter : str
            A twitter object
        """
        self.user_id = user_id
        self.db = db_file
        self.jekyll_source = jekyll_source
        self.jekyll_target = jekyll_target
        self.twitter = twitter
        self.sftp = sftp
        self.jekyll = Jekyll(self.jekyll_source, self.jekyll_target)
        self.scheduler = BackgroundScheduler()

        self.min_tweet_id = 0 # keep at 0 to have ALL tweets processed on startup
        self.calling = False
        try:
            update_interval = int(update_interval)
        except ValueError:
            logging.warning("Update interval is not specified or not an integer. Using default value.")
            update_interval = 1 # (default)
        logging.info("Starting background update job with interval {}h".format(update_interval))
        self.scheduler.add_job(self.callback, 'interval', hours=update_interval, replace_existing=True)
        self.scheduler.start()

    def stop(self):
        """Stop the cron service
        """
        self.scheduler.shutdown()

    def callback(self):
        """Callback that performs jekyll builds and git pushes

        This callback is executed by the scheduler in regular intervals.  Call
        this function directly to perform updates outside from the interval.
        This function obtains the latest tweets, builds jekyll post entries,
        builds a jekyll blog and pushes all changes via git.

        """
        if self.calling:
            logging.warning("""Update-Callback was executed while another \
callback is still running. Aborting""")
            return
        self.calling = True
        try:
            logging.info("Update started. Adding tweets with id > {}".format(self.min_tweet_id))

            # GIT -------------
            source_git = Git(self.jekyll_source)
            source_git.checkout('master')
            source_git.pull()

            # TWITTER ---------
            max_tweet_id = self.twitter.get_max_tweet_id()
            self.twitter.archive_later_than(max_tweet_id)
            # no new tweets? dont sync!
            if max_tweet_id == self.twitter.get_max_tweet_id() and self.min_tweet_id != 0:
                logging.info("No new tweets since last check. Latest tweet id: {}".format(max_tweet_id))
                self.calling = False
                return

            # PROCESS ---------
            conn = sqlite3.connect(self.db)
            refine = Refine(self.user_id, conn)
            obj_list = refine.refine(self.min_tweet_id)
            conn.close()
            for obj in obj_list:
                filecreator.create(self.jekyll_source, obj)
                self.min_tweet_id = max(self.min_tweet_id, int(obj['tweet_id']))

            # JEKYLL ----------
            self.jekyll.build()

            # SYNC ------------
            source_git.push("new blog posts")

            # SYNC DIFFS ------
            if self.sftp:
                self.sftp.update()

            logging.info("Update finished. Added tweets with id < {}".format(self.min_tweet_id))
        finally:
            self.calling = False
