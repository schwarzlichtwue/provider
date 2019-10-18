#!/bin/python3

try:
	from provider.twitter.twitter import Twitter
	#import provider.facebook.facebook as facebook
	from provider.push.cron import Cron
except ImportError:
	from twitter.twitter import Twitter
	#import facebook.facebook as facebook
	from push.cron import Cron
import sys
import argparse
import decouple

def main():
	parser = argparse.ArgumentParser(description="Process new facebook-posts and tweets")
	parser.add_argument('-e', '--env', dest='env_file', type=str,
						help="the location env variables are stored in")
	parser.add_argument('-d', '--database', dest='db_file', type=str,
						help="The database all posts and tweets are stored in. Specify a non-existing file to save a new database there")
	parser.add_argument('-s', '--ssh', dest='ssh_file', type=str,
						help="The ssh key-file to use for pushing to github (needs to allow no passphrase)")
	parser.add_argument('-u', '--update-interval', dest='github_update_interval', type=int,
						help="The interval (h) in which changes are to be pushed via github")
	parser.add_argument('-g', '--github-repository', dest='github_folder', type=str,
						help="The path of the github repository the changes are to be committed to")
	args = parser.parse_args()
	if not args.env_file:
		print("No .env file specified")
		return 1
	if not args.db_file:
		print("No database file specified")
		return 1
	if not args.ssh_file:
		print("No ssh key file specified")
		return 1
	config = decouple.Config(decouple.RepositoryEnv(args.env_file))
	try:
		twitter_consumer_key    = config.get('TWITTER_CONSUMER_KEY')
		twitter_consumer_secret = config.get('TWITTER_CONSUMER_SECRET')
		twitter_access_token    = config.get('TWITTER_ACCESS_TOKEN')
		twitter_access_secret   = config.get('TWITTER_ACCESS_SECRET')
		twitter_user_id         = config.get('TWITTER_USER_ID')
	except UndefinedValueError:
		print("""{} must contain values for TWITTER_USER_ID,
TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_SECRET""".format(args.env_file))
		return 1

	cron = Cron(user_id = twitter_user_id,
				db_file = args.db_file,
				ssh_file = args.ssh_file,
				update_interval = args.github_update_interval,
				folder = args.github_folder)
	# twitter stays 'always on' because it actively listens on the stream
	twitter = Twitter(user_id = twitter_user_id, consumer_key = twitter_consumer_key, consumer_secret =
		twitter_consumer_secret, access_token = twitter_access_token,
		access_secret = twitter_access_secret, db_file = args.db_file)

	twitter.listen()
#	twitter.add_status_to_db(1182370756816179202)
#	twitter.archive(750)

	while True:
		cron.callback()
		input()

main()
