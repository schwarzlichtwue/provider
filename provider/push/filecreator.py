import os
import yaml
from datetime import datetime

def create(folder, obj):
    filename = str(datetime.fromisoformat(obj['date']).date()) + '-' + str(obj['tweet_id']) + '.md'
    path = os.path.join(folder, '_posts', filename)
    yaml_obj = {
        'layout': 'post',
        'categories': 'twitter',
        'title': obj['tweet_id'],
        'date': obj['date'],
        'teaser': obj['teaser'],
        'ref': obj['url']
    }
    if len(obj['tags']) > 0:
        yaml_obj['tags'] = list(set([tag.lower() for tag in obj['tags']]))
    if len(obj['media']) > 0:
        yaml_obj['media'] = [\
            {'file':__store_media__(folder, media)} for media in obj['media']]
    with open(path, 'w') as file_:
        file_.write('---\n')
        file_.write(yaml.dump(yaml_obj))
        file_.write('---\n')
        file_.write(obj['text'])

def __store_media__(folder, media) -> str:
    file_path = os.path.join(folder, 'media', str(media['id']) + '.jpg')
    with open(file_path, 'wb') as file_:
        file_.write(media['data'])
    return os.path.join('/', 'media', str(media['id']) + '.jpg')
