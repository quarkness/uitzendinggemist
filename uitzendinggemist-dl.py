"""Naval Fate.

Usage:
  uitzendinggemist-dl.py <url>...


Options:
  -h --help     Show this screen.

"""
from docopt import docopt
from uitzendinggemist import Aflevering, Serie

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Uitzending Gemist 1.0')
    for url in arguments['<url>']:
        if 'rss' not in url:
            a = Aflevering.by_url(url)
            print a.bestandsnaam
            a.download()
        else:
            s = Serie.by_rss(url)
