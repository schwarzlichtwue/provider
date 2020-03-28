import re

class Shell:

    cat_pattern = re.compile('(?<=\s#)\w*|(?<=^#)\w*')

    def __init__(self, conn, tweet_id: int, text: str, user_id: int,
        user_name: str, user_screen_name: str, created_at: str,
        reply_to_status_id, quoted_status_id):
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

    def status_reply_root(self):
        """
        Return the root status this tweet replies to. If the tweet
        itself is a root status, return self.
        """
        if self.reply_to_status:
            return self.reply_to_status.status_reply_root()
        return self

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
## The following is uncommented to NOT have previously posted media show up
## in quote-tweets
#        if self.quoting and self.quoting.user_id == self.user_id:
#            media_ += self.quoting.__media_helper__(visited)
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
        c.execute('SELECT display_url, url FROM tweet_urls WHERE tweet_id = ?;', (self.id, ))
        rows = c.fetchall()
        url_dict = {}
        for row in rows:
            url_dict[row[0]] = row[1]
        for url in url_dict:
            self.text = self.text.replace(url,
                        '[' + str(url) + '](' + str(url_dict[url]) + ')'
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

        # remove ugly t.co/urls
        p = re.compile('https:\/\/t.co\/[^\s]*')
        for match in set(p.findall(self.text)):
            self.text = self.text.replace(match, '')

        # remove thread counters
        p = re.compile('\s\[?\d+\/\d+\]?')
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
            separator = '\n'
            replied_text = self.replied_by_statuses[0].render_text()
            if self.text.endswith("…"):
                self.text = self.text.replace('…', '')
                if replied_text.startswith("…"):
                    replied_text = replied_text.replace('…', '')
                separator = ' '
            self.text += separator + replied_text

        return self.text

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str({'id': self.id, 'text': self.text})
