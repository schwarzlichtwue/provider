import sqlite3
import urllib.request
import logging

def process_user(cursor, user):
    """Add a twitter user to the database.

    Adds a tweepy.User to the database if it does not already exist

    Parameters
    ----------

    cursor : sqlite3.Cursor
        The sqlite3 cursor sql-queries are executed on.
    user : tweepy.User
        The twitter user that will be added to the database.
    """
    logging.info("Adding user @{}".format(user.screen_name))
    id = user.id
    name = user.name
    screen_name = user.screen_name
    description = user.description
    image_url = user.profile_image_url_https
    image_data = urllib.request.urlopen(image_url).read()
    try:
        datetime_ = user.created_at
    except AttributeError:
        logging.warning("""No information about the user {}'s creation date. \
Using system time""".format(user.screen_name))
        datetime_  = datetime.now()
    iso_date = datetime_.strftime('%Y-%m-%d %H:%M:%S')
    user_row = (id, name, screen_name, sqlite3.Binary(image_data), iso_date, description)
    cursor.execute('INSERT OR IGNORE INTO users  (user_id, name, screen_name, image, created_at, description)  VALUES (?, ?, ?, ?, ?, ?)', user_row)
