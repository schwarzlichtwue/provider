import sqlite3
import urllib.request

def process_user(cursor, user):
	id = user.id
	name = user.name
	screen_name = user.screen_name
	description = user.description
	image_url = user.profile_image_url_https
	image_data = urllib.request.urlopen(image_url).read()
	try:
		datetime_ = user.created_at
	except AttributeError:
		datetime_  = datetime.now()
	iso_date = datetime_.strftime('%Y-%m-%d %H:%M:%S')
	user_row = (id, name, screen_name, sqlite3.Binary(image_data), iso_date, description)
	cursor.execute('INSERT OR IGNORE INTO users  (user_id, name, screen_name, image, created_at, description)  VALUES (?, ?, ?, ?, ?, ?)', user_row)
