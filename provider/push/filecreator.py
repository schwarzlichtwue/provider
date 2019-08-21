import os
from datetime import datetime

def create(folder, obj):
	filename = str(datetime.fromisoformat(obj['date']).date()) + '-' + str(obj['tweet_id']) + '.md'
	path = os.path.join(folder, filename)
	with open(path, 'w') as file_:
		file_.write('---\n')
		file_.write('layout: post\n')
		file_.write('date: \'{}\'\n'.format(obj['date']))
		file_.write('categories: {}\n'.format(' '.join(sorted(obj['categories']))).lower())
		file_.write('ref: \'{}\'\n'.format(obj['url']))
		file_.write('---\n')
		file_.write(obj['text'])
