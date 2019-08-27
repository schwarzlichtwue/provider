try:
	from provider.push.tweet.shell import Shell
	from provider.push.tweet.shells import ShellTree
except ImportError:
	from push.tweet.shell import Shell
	from push.tweet.shells import ShellTree

class Refine():

	def __init__(self, user_id, conn):
		self.user_id = user_id
		self.conn = conn
		self.shell_tree = ShellTree()
		self.user_names = {}

	def __get_user_name__(self, user_id):
		if user_id not in self.user_names:
			c = self.conn.cursor()
			c.execute("""SELECT name, screen_name FROM users WHERE user_id = ? LIMIT 1;""", (user_id, ))
			rows = c.fetchall()
			if len(rows) >= 1:
				self.user_names[user_id] = {'user_name': rows[0][0], 'screen_name': rows[0][1]}
			else:
				self.user_names[user_id] = {'user_name': 'User not found', 'screen_name': 'undefined'}
		return self.user_names[user_id]['user_name'], self.user_names[user_id]['screen_name']


	def __prepare_shell_tree__(self):
		c = self.conn.cursor()
		c.execute("""SELECT tweet_id, text, user_id, created_at, reply_to_status, quoted_status_id FROM tweets""")
		rows = c.fetchall()
		for row in rows:
			user_name, user_screen_name = self.__get_user_name__(row[2])
			shell = Shell(
				conn = self.conn,
				tweet_id = row[0],
				text = row[1],
				user_id = row[2],
				user_name = user_name,
				user_screen_name = user_screen_name,
				created_at = row[3],
				reply_to_status_id = row[4],
				quoted_status_id = row[5],
			)
			self.shell_tree.add_shell(shell)

	def refine(self):
		self.__prepare_shell_tree__()
		self.shell_tree = self.shell_tree.filter_by_id(self.user_id)
		self.shell_tree = self.shell_tree.filter_for_roots()
		obj_list = []
		for tweet_id in self.shell_tree:
			tweet_shell = self.shell_tree[tweet_id]
			obj = {}
			obj['tweet_id'] = tweet_id
			obj['date'] = tweet_shell.created_at
			obj['url'] = 'https://twitter.com/{}/status/'.format(tweet_shell.user_name) + str(tweet_id)
			obj['categories'] = tweet_shell.categories()
			obj['text'] = tweet_shell.render_text()
			obj_list += [obj]
		return obj_list
