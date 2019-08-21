import re

class El(object):

	def __init__(self, conn, top_tweet):
		self.conn = conn
		self.top_tweet = top_tweet
		self.cat_pattern = re.compile('(?<=\s#)\w*|(?<=^#)\w*')
		self.status_url_pattern = re.compile('^(http(s)?:\/\/)?(www\.)?twitter\.com')

	def categories(self) -> list:
		cats = []
		tweet = self.top_tweet
		while True:
			cats += self.cat_pattern.findall(tweet['text'])
			if 'quoting' in tweet:
				cats += self.cat_pattern.findall(tweet['quoting']['text'])
			if 'replied_by' in tweet:
				tweet = tweet['replied_by']
			else:
				break
		for i,_ in enumerate(cats):
			cats[i] = cats[i].replace(' ', '')
		return list(set(cats))

	def clean_text(self, text) -> str:
		# replace hashtags with urls:
		p = re.compile('(?<=\s)#\w*|(?<=^)#\w*')
		new_text = (text+'.')[:-1]
		for match in set(p.findall(new_text)):
			new_text = new_text.replace(match,
				'[' + match + '](/t/{})'.format(match.replace('#', '').lower())
			)
		# replace usernames with urls:
		p = re.compile('(?<=\s)@\w*|(?<=^)@\w*')
		for match in set(p.findall(new_text)):
			new_text = new_text.replace(match,
				'[' + match + '](https://twitter.com/{})'.format(match.replace('@', ''))
			)
		# replace * with \*
		new_text = new_text.replace('*', '\\*')
		p = re.compile('\d+/\d+')
		for match in set(p.findall(new_text)):
			new_text = new_text.replace(match, '')
		new_text = new_text.replace('\n', '\n\n')
		return new_text

	def clean_quote(self, user_id, text) -> str:
		quote = ''
		c = self.conn.cursor()
		c.execute('SELECT name, screen_name FROM users WHERE user_id = ? LIMIT 1;', (user_id, ))
		rows = c.fetchall()
		if len(rows) >= 1:
			quote += '> {} ([@{}](https://twitter.com/{})):  \n'.format(rows[0][0], rows[0][1], rows[0][1])
		lines = self.clean_text(text).split('\n')
		for line in lines:
			quote += '>' + line + '  \n'
		return quote

	def clean_url(self, tweet_id, text) -> str:
		# make urls clickable
		new_text = (text+'.')[:-1]
		c = self.conn.cursor()
		c.execute('SELECT DISTINCT display_url, url FROM tweet_urls WHERE tweet_id = ?;', (tweet_id, ))
		rows = c.fetchall()
		for row in rows:
			#if self.status_url_pattern.match(row[1]):
			new_text = new_text.replace(row[0],
						'[' + row[0] + '](' + row[1] + ')'
					)
		return new_text

	def render_text(self) -> str:
		text = ''
		tweet = self.top_tweet
		while True:
			text += self.clean_text(
						self.clean_url(tweet['tweet_id'], tweet['text'])
					) + '\n'
			if 'quoting' in tweet:
				text += '\n'
				text += self.clean_quote(tweet['quoting']['user_id'],
						self.clean_url(tweet['quoting']['tweet_id'], tweet['quoting']['text']))
				text += '\n'

			if 'replied_by' in tweet:
				text += '\n'
				tweet = tweet['replied_by']
			else:
				break
		return text

def process(user_id, cursor, rows):
	def __recurse__(row, map_, id, new_id):
		"""
		if row referenced by row[id] exists in map_, remove row[id] and
		add row[new_id] with the value of map_[row[id]]
		"""
		if row[id] is not None:
			try:
				id_obj = map_[row[id]]
				row[new_id] = id_obj
			except KeyError:
				pass
			try:
				row.pop(id)
			except KeyError:
				pass

	tweet_map = {}
	for row in rows:
		tweet_map[row['tweet_id']] = row
	for tweet_id in tweet_map:
		if tweet_map[tweet_id]['reply_to_status'] is not None:
			if str(tweet_map[tweet_id]['user_id']) == str(user_id):
				try:
					tweet_map[ tweet_map[tweet_id]['reply_to_status'] ]['replied_by'] = tweet_map[tweet_id]
				except KeyError:
					pass
	tweet_map_ = {}
	for tweet_id in tweet_map:
		if tweet_map[tweet_id]['reply_to_status'] is None:
			if str(tweet_map[tweet_id]['user_id']) == str(user_id):
				tweet_map_[tweet_id] = tweet_map[tweet_id]
	tweet_map = tweet_map_
	for tweet_id in tweet_map:
		__recurse__(tweet_map[tweet_id], tweet_map, 'quoted_status_id', 'quoting')
	obj_list = []
	for tweet_id in tweet_map:
		tweet = tweet_map[tweet_id]
		obj = {}
		obj['tweet_id'] = tweet_id
		obj['date'] = tweet['created_at']
		obj['url'] = 'https://twitter.com/schwarzlichtwue/status/' + str(tweet_id)
		el = El(cursor, tweet)
		obj['categories'] = el.categories()
		obj['text'] = el.render_text()
		obj_list += [obj]
	return obj_list
