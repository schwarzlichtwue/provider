import os
from datetime import datetime

def create(folder, obj):
	filename = str(datetime.fromisoformat(obj['date']).date()) + '-' + str(obj['tweet_id']) + '.md'
	path = os.path.join(folder, '_posts', filename)
	with open(path, 'w') as file_:
		file_.write('---\n')
		file_.write('layout: post\n')
		file_.write('date: \'{}\'\n'.format(obj['date']))
		file_.write('categories: {}\n'.format(' '.join(sorted(obj['categories']))).lower())
		file_.write('ref: \'{}\'\n'.format(obj['url']))
		if 'media' in obj:
			file_.write('media: ')
			for media in obj['media']:
				media_path = __store_media__(folder, media)
				file_.write('{} '.format(media_path))
			file_.write('\n')
		file_.write('---\n')
		file_.write(obj['text'])

def __store_media__(folder, media) -> str:
	file_path = os.path.join(folder, 'media', str(media['id']) + '.jpg')
	with open(file_path, 'wb') as file_:
		file_.write(media['data'])
	return os.path.join('/', 'media', str(media['id']) + '.jpg')
