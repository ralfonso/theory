"""The application's Globals object"""

from theory.model.mpdpool import MPDPool
from theory.model.tconfig import TConfig
from pylons import config


class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """

    searchterms = ['Artist','Title','Album','Genre','Any']

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable
        """

        self.tc = TConfig()
        self.p = MPDPool(self)
        self.get_genres()

    def get_genres(self):
        """ load all tracks and create a list of every unique genre in the database"""
        self.genres = set()

        # this won't work before configuration
        try:
            m = self.p.connect()
            all_tracks = m.listallinfo()
            
            for t in all_tracks:
                if not 'genre' in t:
                    continue

                if type(t['genre']) == list:
                    track_genres = t['genre']
                else:
                    track_genres = [t['genre']]

                for genre in track_genres:
                    self.genres.add(genre)
            
            m.disconnect()
        except:
            pass
