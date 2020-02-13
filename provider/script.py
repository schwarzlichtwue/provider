#!/bin/python3

try:
    from provider.push.sftp import Sftp
    from provider.twitter.twitter import Twitter
    from provider.push.cron import Cron
except ImportError:
    from twitter.twitter import Twitter
    from push.sftp import Sftp
    from push.cron import Cron
import sys
import time
import signal
import argparse
import decouple
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Content Provider initiated")
    # cl flags:
    # --env MANDATORY
    # --database MANDATORY
    # --jekyll-source MANDATORY.
    # --jekyll-target MANDATORY.
    # --update-interval OPTIONAL
    # --sftp-address OPTIONAL. If not specified, changes are not pushed to a SFTP server
    # --sftp-batch OPTIONAL. But MANDATORY if --sftp-address is specified
    # --sftp-config OPTIONAL. But MANDATORY if --sftp-address is specified
    parser = argparse.ArgumentParser(description="Process new facebook-posts and tweets")
    parser.add_argument('-e', '--env', dest='env_file', type=str,
                help="the location env variables are stored in")
    parser.add_argument('-d', '--database', dest='db_file', type=str,
                help="The database all posts and tweets are stored in. Specify a non-existing file to save a new database there")
    parser.add_argument('-a', '--sftp-address', dest='sftp_address', type=str,
                help="The sftp address")
    parser.add_argument('-b', '--sftp-batch', dest='sftp_batch_file', type=str,
                help="The sftp batch file to use for uploading data")
    parser.add_argument('-c', '--sftp-config', dest='sftp_config_file', type=str,
                help="The ssh config file to use for connecting via sftp")
    parser.add_argument('-u', '--update-interval', dest='github_update_interval', type=int,
                help="The interval (h) in which changes are to be pushed")
    parser.add_argument('--jekyll-source', dest='jekyll_source', type=str,
                help="The path of the github repository the source changes are to be committed to")
    parser.add_argument('--jekyll-target', dest='jekyll_target', type=str,
                help="The path of the github repository the target changes are to be committed to")
    args = parser.parse_args()
    if not args.env_file:
        logging.error("No .env file specified")
        return 1
    if not args.db_file:
        logging.error("No database file specified")
        return 1
    if not args.jekyll_source:
        logging.error("Missing jekyll source folder")
        return 1
    if not args.jekyll_target:
        logging.error("Missing jekyll target folder")
        return 1
    if not args.sftp_address:
        logging.warning("No SFTP address specified. Changes will not be uploaded")
    else:
        if not args.sftp_batch_file:
            logging.error("SFTP Address is specified, but SFTP batch file is not.")
            return 1
        if not args.sftp_config_file:
            logging.error("SFTP Address is specified, but SSH config file is not.")
            return 1

    config = decouple.Config(decouple.RepositoryEnv(args.env_file))
    try:
        twitter_consumer_key    = config.get('TWITTER_CONSUMER_KEY')
        twitter_consumer_secret = config.get('TWITTER_CONSUMER_SECRET')
        twitter_access_token    = config.get('TWITTER_ACCESS_TOKEN')
        twitter_access_secret   = config.get('TWITTER_ACCESS_SECRET')
        twitter_user_id         = config.get('TWITTER_USER_ID')
    except UndefinedValueError:
        logging.error("""{} must contain values for TWITTER_USER_ID,
TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_SECRET""".format(args.env_file))
        return 1

    sftp_password = None
    if args.sftp_address:
        try:
            sftp_password = config.get('SFTP_PASSWORD')
        except UndefinedValueError:
            logging.error("{} must contain an entry for SFTP_PASSWORD".format(args.env_file))
            return 1

    twitter = Twitter(user_id = twitter_user_id,
        consumer_key          = twitter_consumer_key,
        consumer_secret       = twitter_consumer_secret,
        access_token          = twitter_access_token,
        access_secret         = twitter_access_secret,
        db_file               = args.db_file
        )

    sftp = Sftp(
        address     = args.sftp_address,
        batch_file  = args.sftp_batch_file,
        config_file = args.sftp_config_file,
        password    = sftp_password
        )

    cron = Cron(user_id = twitter_user_id,
        db_file         = args.db_file,
        update_interval = args.github_update_interval,
        jekyll_source   = args.jekyll_source,
        jekyll_target   = args.jekyll_target,
        sftp            = sftp,
        twitter         = twitter
        )

    cron.callback()

    # cron is running with the specified update interval. The tool is running
    # inside a docker container, so how do we skip forward and perform an
    # update outside the interval? By sending a custom command to the tools's
    # process!
    # Assuming the PID is 1, the following command performs a manual update:
    # $ kill -s SIGUSR1 1
    def update_handler(signum, frame):
        logging.info("Manual Push started")
        cron.callback()
    signal.signal(signal.SIGUSR1, update_handler)
    logging.info("Update-Handler for SIGUSR1 registered")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.warning("Caught SIGINT signal. Stopping")
    finally:
        cron.stop()

main()
