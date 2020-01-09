from datetime import datetime
import requests
import sqlite3
import logging
try:
    import twitter.user as user_processor
except ImportError:
    import provider.twitter.user as user_processor

class StatusProcessor():

    def __init__(self, db):
        self.conn = sqlite3.connect(db)

    def process_status(self, status):
        """
        Adds a given status and linked media to the database
        Only call this method from the same thread! This is dictated
        by the sqlite connection
        """
        logging.info("Processing status {}".format(status.id))
        cursor = self.conn.cursor()
        #print(status)

        try:
            user_processor.process_user(cursor, status.author)
        except Exception:
            pass

        status_id        = status.id
        reply_to_status  = status.in_reply_to_status_id
        reply_to_user    = status.in_reply_to_user_id
        quoted_status_id = None
        if status.is_quote_status:
            quoted_status_id = status.quoted_status_id
            try:
                self.process_status(status.quoted_status)
            except (KeyError, AttributeError):
                pass
        datetime_ = None
        try:
            datetime_ = status.created_at
        except (KeyError, AttributeError):
            datetime_  = datetime.now()
        iso_date = datetime_.strftime('%Y-%m-%d %H:%M:%S')

        user_id = None
        try:
            user_id = status.author.id
        except (KeyError, AttributeError):
            pass

        try:
            text = status.full_text
        except (KeyError, AttributeError):
            try:
                text = status.extended_tweet['full_text']
            except (KeyError, AttributeError):
                try:
                    text = status.text
                except (KeyError, AttributeError):
                    return

        entities = {}
        try:
            entities = status.extended_entities
        except (KeyError, AttributeError):
            try:
                entities = status.extended_tweet['extended_entities']
            except (KeyError, AttributeError):
                try:
                    entities = status.entities
                except (KeyError, AttributeError):
                    try:
                        entities = status.extended_tweet['entities']
                    except (KeyError, AttributeError):
                        pass

        hashtags = []
        if 'hashtags' in entities:
            for entity in entities['hashtags']:
                hashtags += [(entity['text'], status_id)]
        urls = []
        if 'urls' in entities:
            for entity in entities['urls']:
                urls += [(entity['display_url'],
                    entity['expanded_url'], status_id)]
                try:
                    text = text.replace(entity['url'], entity['display_url'])
                except (KeyError, AttributeError):
                    pass

        media = []
        if 'media' in entities:
            for entity in entities['media']:
                url = ''
                try:
                    url = entity['media_url_https']
                except (KeyError, AttributeError):
                    url = entity['media_url']
                image_blob = None
                try:
                    image_blob = requests.request(url=url, method='get').content
                except Exception:
                    continue
                media += [(entity['id'], status_id, 0, image_blob)]

        tweet_row = (status_id, text, user_id, iso_date, reply_to_status, reply_to_user, quoted_status_id)
        cursor.execute('INSERT OR IGNORE INTO tweets (tweet_id, text, user_id, created_at, reply_to_status, reply_to_user, quoted_status_id)  VALUES (?, ?, ?, ?, ?, ?, ?)', tweet_row)
        cursor.executemany('INSERT OR IGNORE INTO tweet_tags (tag_name, tweet_id)  VALUES (?, ?)', hashtags)
        cursor.executemany('INSERT OR IGNORE INTO tweet_urls (display_url, url, tweet_id)  VALUES (?, ?, ?)', urls)
        cursor.executemany('INSERT OR IGNORE INTO tweet_media (media_id, tweet_id, is_video, data)  VALUES (?, ?, ?, ?)', media)
        self.conn.commit()
