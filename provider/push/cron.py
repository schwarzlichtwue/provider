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

    def __init__(self, user_id: int, db_file: str, ssh_file: str,
            update_interval: int, jekyll_source: str, jekyll_target: str):
        self.user_id = user_id
        self.db = db_file
        self.ssh_file = ssh_file
        self.jekyll_source = jekyll_source
        self.jekyll_target = jekyll_target

        self.jekyll = Jekyll(self.jekyll_source, self.jekyll_target)
        self.scheduler = BackgroundScheduler()

        self.min_tweet_id = 0
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

        logging.info("Update finished. Added tweets with id < {}".format(self.min_tweet_id))
