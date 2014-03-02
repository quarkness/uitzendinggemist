from collections import defaultdict
import re
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

    def __init__(self, nebo_id='POMS_S_VPRO_465233'):
        super(Serie, self).__init__()
        self.nebo_id = nebo_id
        self.data_url = 'http://apps-api.uitzendinggemist.nl/series/{}.json'.format(self.nebo_id)
        self.load()

    def __unicode__(self):
        return '{} [{}]'.format(self.naam, self.nebo_id)

    @property
    def naam(self):
        return self.data['name']

    @property
    def beschrijving(self):
        return self.data['description']

    @property
    def afleveringen(self):
        return [Aflevering(a['nebo_id'], a['name'], self) for a in self.data['episodes']]


class Aflevering(UitzendingGemist):
    def __init__(self, nebo_id, naam='', serie=None, serie_naam=None):
        super(Aflevering, self).__init__()
        self.playerid = nebo_id
        self.naam = naam
        self.serie = serie
        self.serie_naam = serie_naam

    def __unicode__(self):
        return '{} - {} [{}]'.format(self.serienaam, self.naam, self.playerid)

    @property
    def serienaam(self):
        if self.serie:
            return self.serie.naam
        else:
            return self.serie_naam

    @property
    def bestandsnaam(self):
        return '{} - {} - {}.mp4'.format(self.serienaam, self.naam, self.playerid)

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
            for i, chunk in enumerate(r.iter_content(chunk_size=1024)):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    if i % 10 == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                    f.flush()
