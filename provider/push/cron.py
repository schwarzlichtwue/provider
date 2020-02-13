import os
import sqlite3
import logging

from apscheduler.schedulers.background import BackgroundScheduler

try:
    from provider.push.git import Git
    from provider.push.sftp import Sftp
    from provider.push.jekyll import Jekyll
    from provider.push.refine import Refine
    import provider.push.filecreator as filecreator
except ImportError:
    from push.git import Git
    from push.sftp import Sftp
    from push.jekyll import Jekyll
    from push.refine import Refine
    import push.filecreator as filecreator

class Cron:

    def __init__(self, user_id: int, db_file: str, ssh_file: str,
            update_interval: int, jekyll_source: str, jekyll_target: str,
            sftp_address: str, sftp_password: str, sftp_config_file: str):
        """Start a scheduler which pushes jekyll changes at regular intervals

        Creates a jekyll instance and registers a background (async) scheduler
        to perform jekyll builds and git pushes at regular intervals

        Parameters
        ----------

        user_id : int
            The twitter user's id
        db_file : str
            The sqlite3 database
        ssh_file : str
            An ssh private-key file authorized to push to the git repository
        update_interval : int
            The update interval (in hours) by which the scheduler is configured
        jekyll_source : str
            The folder where jekyll source files are located at.
            Cron performes pushes for any changes made here
        jekyll_target : str
            The folder where jekyll is built in.
            Cron performes pushes for any changes made here
        sftp_address : str
            The address to connect to via SFTP
        sftp_password : str
            The password required for connecting via SFTP
        sftp_config_file : str
            The ssh config file for specifying the sftp connection
        """
        self.user_id = user_id
        self.db = db_file
        self.ssh_file = ssh_file
        self.jekyll_source = jekyll_source
        self.jekyll_target = jekyll_target

        self.sftp = None
        if sftp_address:
            self.sftp = Sftp(folder = self.jekyll_target,
                address = sftp_address,
                password = sftp_password,
                config_file = sftp_config_file)

        self.jekyll = Jekyll(self.jekyll_source, self.jekyll_target)
        self.scheduler = BackgroundScheduler()

        self.min_tweet_id = 0 # keep at 0 to have ALL tweets processed on startup
        self.calling = False
        try:
            update_interval = int(update_interval)
        except ValueError:
            logging.warning("Update interval is not an integer. Using default value.")
            update_interval = 2 # (default)
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
            conn = sqlite3.connect(self.db)

            refine = Refine(self.user_id, conn)
            obj_list = refine.refine(self.min_tweet_id)

            conn.close()

            source_git = Git(self.jekyll_source, self.ssh_file)
            source_git.checkout('dev')
            source_git.pull()

            target_git = Git(self.jekyll_target, self.ssh_file)
            target_git.checkout('master')
            target_git.pull()

            for obj in obj_list:
                filecreator.create(self.jekyll_source, obj)
                self.min_tweet_id = max(self.min_tweet_id, int(obj['tweet_id']))

            source_git.push("new blog posts")

            self.jekyll.build()
            target_git.push("new tweets")

            if self.sftp:
                self.sftp.update()

            logging.info("Update finished. Added tweets with id < {}".format(self.min_tweet_id))
        finally:
            self.calling = False
