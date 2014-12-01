"""Naval Fate.

Usage:
  uitzendinggemist-dl.py <url>...


Options:
  -h --help     Show this screen.

"""
from docopt import docopt
from uitzendinggemist import Episode, Serie

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Uitzending Gemist 1.0')
    for url in arguments['<url>']:
        if 'rss' not in url:
            episode = Episode.by_url(url)
            print(episode.filename)
            episode.download()
        else:
            serie = Serie.by_rss(url)
