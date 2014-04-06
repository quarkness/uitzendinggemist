from collections import defaultdict
import re
from bs4 import BeautifulSoup
from clint.textui import progress
import requests
import sys

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36'

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
        self.afleveringen = []
        if nebo_id:
            self.nebo_id = nebo_id
            self.data_url = 'http://apps-api.uitzendinggemist.nl/series/{}.json'.format(self.nebo_id)
            self.load()
            self.afleveringen = [Aflevering(a['nebo_id'], a['name'], self) for a in self.data['episodes']]
            self.naam = self.data['name']
            self.beschrijving = self.data['description']

    def __unicode__(self):
        return '{} [{}]'.format(self.naam, self.nebo_id)

    @staticmethod
    def by_rss(url, limit=10):
        serie = Serie()
        rss = BeautifulSoup(UitzendingGemist().rs.get(url).content, "xml")
        for item in rss.find_all('item')[:limit]:
            print item.title.text
            print item.link.text
            nebo_id = item.guid.text.replace('http://gemi.st/', '')
            naam = ' - '.join(item.title.text.split(' - ')[1:])
            aflevering = Aflevering(nebo_id, naam=naam, serie_naam=rss.channel.title.text)
            serie.afleveringen.append(aflevering)
        return serie

class Aflevering(UitzendingGemist):
    def __init__(self, nebo_id, naam='', serie=None, serie_naam=None):
        super(Aflevering, self).__init__()
        self.playerid = nebo_id
        self.naam = naam
        self.serie = serie
        self.serie_naam = serie_naam

    def __unicode__(self):
        return '{} - {} [{}]'.format(self.serienaam, self.naam, self.playerid)

    @staticmethod
    def by_url(url):
        h = requests.get(url)
        soup = BeautifulSoup(h.content)
        s = soup.find('span', {'id': 'episode-data'})
        nebo_id = s.attrs['data-player-id']
        meta = soup.find('div', {'id': 'meta-information'})

        serie_naam = meta.h1.a.text
        naam = meta.h2.a.text
        return Aflevering(nebo_id, naam, serie_naam=serie_naam)

    @property
    def serienaam(self):
        if self.serie:
            return self.serie.naam
        else:
            return self.serie_naam

    @property
    def bestandsnaam(self):
        return u'{} - {} - {}.mp4'.format(self.serienaam, self.naam, self.playerid).replace('/', '_')

    def get_token(self):
        data = self.rs.get('http://ida.omroep.nl/npoplayer/i.js').content
        return re.compile('.token\s*=\s*"(.*?)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)

    def get_streams(self, token):
        url = 'http://ida.omroep.nl/odi/?prid={}&puboptions=h264_bb,h264_std,h264_sb&adaptive=no&part=1&token={}'.format(self.playerid, token)
        return self.rs.get(url).json()['streams']

    def get_url(self):
        token = self.get_token()
        streams = self.get_streams(token)
        json_url = streams[0].replace('jsonp', 'json')
        print 'json_url: {}'.format(json_url)
        url = self.rs.get(json_url).json()['url']
        print 'url: {}'.format(url)
        return url

    def download(self):
        url = self.get_url()
        r = self.rs.get(url, stream=True)
        print r.status_code
        with open(self.bestandsnaam, 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        print ''
