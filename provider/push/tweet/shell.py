import re

class Shell:

	cat_pattern = re.compile('(?<=\s#)\w*|(?<=^#)\w*')

	def __init__(self, conn, tweet_id: int, text: str, user_id: int, user_name: str, user_screen_name: str, created_at: str, reply_to_status_id, quoted_status_id):
		self.conn = conn
		self.id = tweet_id
		self.text = text
		self.original_text = (text + '.')[:-1]
		self.user_id = user_id
		self.user_name = user_name
		self.user_screen_name = user_screen_name
		self.created_at = created_at

		self.reply_to_status_id = reply_to_status_id
		self.reply_to_status = None
		self.replied_by_statuses = []

		self.quoted_status_id = quoted_status_id
		self.quoting = None
		self.quoted_by_statuses = []

		self.rendered = False

	def media(self) -> list:
		return self.__media_helper__([])

	def __media_helper__(self, visited: list) -> list:
		if self.id in visited:
			return []
		else:
			visited += [self.id]
		c = self.conn.cursor()
		c.execute('SELECT DISTINCT media_id, is_video, data FROM tweet_media WHERE tweet_id = ?;', (self.id, ))
		rows = c.fetchall()

		media_ = []
		for row in rows:
			media_ += [{'id': row[0], 'is_video': row[1], 'data': row[2]}]

		for tweet_shell in self.replied_by_statuses:
			if tweet_shell.user_id == self.user_id:
				media_ += tweet_shell.__media_helper__(visited)
		if self.quoting and self.quoting.user_id == self.user_id:
			media_ += self.quoting.__media_helper__(visited)
		return media_

	def categories(self) -> list:
		return self.__categories_helper__([])

	def __categories_helper__(self, visited: list) -> list:
		if self.id in visited:
			return []
		else:
			visited += [self.id]
		cats = self.cat_pattern.findall(self.text)
		for i,_ in enumerate(cats):
			cats[i] = cats[i].replace(' ', '')

		for tweet_shell in self.replied_by_statuses:
			cats += tweet_shell.__categories_helper__(visited)
		if self.quoting:
			cats += self.quoting.__categories_helper__(visited)
		return list(set(cats))

	def __url_cleaner__(self):
		c = self.conn.cursor()
		c.execute('SELECT DISTINCT display_url, url FROM tweet_urls WHERE tweet_id = ?;', (self.id, ))
		rows = c.fetchall()
		for row in rows:
			self.text = self.text.replace(row[0],
						'[' + row[0] + '](' + row[1] + ')'
					)

	def __text_cleaner__(self):
		# replace hashtags with urls:
		p = re.compile('(?<=\s)#\w*|(?<=^)#\w*')
		for match in set(p.findall(self.text)):
			self.text = self.text.replace(match,
				'[' + match + '](/t/{})'.format(match.replace('#', '').lower())
			)
		# replace usernames with urls:
		p = re.compile('(?<=\s)@\w*|(?<=^)@\w*')
		for match in set(p.findall(self.text)):
			self.text = self.text.replace(match,
				'[' + match + '](https://twitter.com/{})'.format(match.replace('@', ''))
			)
		# replace * with \*
		self.text = self.text.replace('*', '\\*')

		# remove those ugly t.co/urls
		p = re.compile('https:\/\/t.co\/[^\s]*')
		for match in set(p.findall(self.text)):
			self.text = self.text.replace(match, '')

		# remove thread counters
		p = re.compile('\[?\d+/\d+\]?')
		for match in set(p.findall(self.text)):
			self.text = self.text.replace(match, '')
		self.text = self.text.replace('\n', '\n\n')

	def __quote__(self):
		quote = '> <b>{} ([@{}](https://twitter.com/{})):</b>  \n'.format(self.quoting.user_name, self.quoting.user_screen_name, self.quoting.user_screen_name)
		lines = self.quoting.render_text().split('\n')
		for line in lines:
			quote += '>' + line + '  \n'
		return quote

	def render_text(self):
		if self.rendered:
			return self.text
		self.rendered = True
		self.__url_cleaner__()
		self.__text_cleaner__()
		if self.quoting:
			quoted_text = self.__quote__()
			self.text += '\n' + quoted_text + '\n'
		if len(self.replied_by_statuses) > 0:
			self.text += '\n\n' + self.replied_by_statuses[0].render_text()

		return self.text

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return str({'id': self.id, 'text': self.text})
