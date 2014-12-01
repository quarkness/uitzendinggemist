from collections import defaultdict
import re
from bs4 import BeautifulSoup
from clint.textui import progress
import requests

# Completed parts shown as MB
progress.BAR_TEMPLATE = BAR_TEMPLATE = '%s[%s%s] %i/%i MB - %s\r'
USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/33.0.1750.117 Safari/537.36')


class UitzendingGemist(object):
    def __init__(self):
        self.rs = requests.Session()
        self.rs.headers.update({'User-Agent': USER_AGENT})
        self.data_url = None
        self.data = defaultdict(None)

    def load(self):
        self.data = self.rs.get(self.data_url).json()


class Serie(UitzendingGemist):

    def __init__(self, nebo_id=None):
        super(Serie, self).__init__()
        self.episodes = []
        if nebo_id:
            self.nebo_id = nebo_id
            self.data_url = ('http://apps-api.uitzendinggemist.nl/'
                             'series/{}.json').format(self.nebo_id)
            self.load()
            self.episodes = [Episode(episode['nebo_id'], episode['name'], self)
                             for episode in self.data['episodes']]
            self.name = self.data['name']
            self.description = self.data['description']

    def __unicode__(self):
        return '{} [{}]'.format(self.name, self.nebo_id)

    @staticmethod
    def by_rss(url, limit=10):
        serie = Episode()
        rss = BeautifulSoup(UitzendingGemist().rs.get(url).content, "xml")
        for item in rss.find_all('item')[:limit]:
            print(item.title.text)
            print(item.link.text)
            nebo_id = item.guid.text.replace('http://gemi.st/', '')
            name = ' - '.join(item.title.text.split(' - ')[1:])
            episode = Episode(
                nebo_id, name=name, serie_name=rss.channel.title.text)
            serie.episodes.append(episode)
        return serie


class Episode(UitzendingGemist):
    def __init__(self, nebo_id, name='', serie=None, serie_name=None):
        super(Episode, self).__init__()
        self.playerid = nebo_id
        self.name = name
        self.serie = serie
        self.serie_name = serie_name

    def __unicode__(self):
        return '{} - {} [{}]'.format(self.serie_name, self.name, self.playerid)

    @staticmethod
    def by_url(url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content)
        nebo_id = url.split('/')[-1]

        serie_name = soup.find(
            'div', {'class': 'row-fluid title-and-broadcasters'}
        ).h1.a.text

        try:
            name = soup.find('div', {'class': 'span-sidebar'}).h2.text
        except AttributeError:  # Episode name is not always available
            name = None

        return Episode(nebo_id, name, serie_name=serie_name)

    @property
    def seriename(self):
        if self.serie:
            return self.serie.name
        else:
            return self.serie_name

    @property
    def filename(self):
        raw_name = (u'{} - {} - {}.mp4'.format(
            self.seriename, self.name, self.playerid) if self.name
            else u'{} - {}.mp4'.format(self.seriename, self.playerid))
        return raw_name.replace('/', '_')

    def get_token(self):
        data = self.rs.get('http://ida.omroep.nl/npoplayer/i.js').content
        return re.compile(
            '.token\s*=\s*"(.*?)"', re.DOTALL + re.IGNORECASE
        ).search(str(data)).group(1)

    def get_streams(self, token):
        url = ('http://ida.omroep.nl/odi/'
               '?prid={}&puboptions=h264_bb,h264_std,h264'
               '_sb&adaptive=no&part=1&token={}').format(self.playerid, token)
        return self.rs.get(url).json()['streams']

    def get_url(self):
        token = self.get_token()
        streams = self.get_streams(token)
        json_url = streams[0].replace('jsonp', 'json')
        print('json_url: {}'.format(json_url))
        url = self.rs.get(json_url).json()['url']
        print('url: {}'.format(url))
        return url

    def download(self):
        url = self.get_url()
        r = self.rs.get(url, stream=True)
        chunk_size = 1024**2  # 1MB
        print('HTTP status code: {}'.format(r.status_code))
        with open(self.filename, 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in progress.bar(
                    r.iter_content(chunk_size=chunk_size),
                    expected_size=(total_length/chunk_size) + 1):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        print('Finished downloading {}'.format(self.filename))
