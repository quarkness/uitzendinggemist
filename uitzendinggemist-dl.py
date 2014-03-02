"""Naval Fate.

Usage:
  uitzendinggemist-dl.py <url>...


Options:
  -h --help     Show this screen.

"""
from docopt import docopt
from uitzendinggemist import Aflevering

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Naval Fate 2.0')
    for url in arguments['<url>']:
        a = Aflevering.by_url(url)
        print a.bestandsnaam
        a.download()
