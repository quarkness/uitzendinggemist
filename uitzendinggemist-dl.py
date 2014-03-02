"""Naval Fate.

Usage:
  uitzendinggemist-dl.py <url>...


Options:
  -h --help     Show this screen.

"""
from docopt import docopt
from uitzendinggemist import Aflevering
import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Naval Fate 2.0')
    for url in arguments['<url>']:
        h = requests.get(url)
        soup = BeautifulSoup(h.content)
        s = soup.find('span', {'id': 'episode-data'})
        nebo_id = s.attrs['data-player-id']
        meta = soup.find('div', {'id': 'meta-information'})

        serie_naam = meta.h1.a.text
        naam = meta.h2.a.text
        a = Aflevering(nebo_id, naam, serie_naam=serie_naam)

        print a.bestandsnaam
        a.download()
