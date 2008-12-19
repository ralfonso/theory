"""The application's Globals object"""

from theory.model.mpdhelper import *
from theory.model.mpdpool import QueuePool
from theory.model.tconfig import TConfig
from pylons import config

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """
    def get_mpd_conn(self):
        m = mpdhelper(self)
        return m

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable
        """

        self.p = QueuePool(self.get_mpd_conn, max_overflow=10, pool_size=2, use_threadlocal=True)
        self.tc = TConfig()
        self.get_genres()
        self.version = config.get('version','')
        pass

    def get_genres(self):
        """ load all tracks and create a list of every unique genre in the database"""
        self.genres = []

        # this won't work before configuration
        try:
            m = self.p.connect()
            all_tracks = m.listallinfo()
            
            for t in all_tracks:
                if not t.has_key('genre'):
                    continue

                if type(t['genre']) == list:
                    track_genres = t['genre']
                else:
                    track_genres = [t['genre']]

                for genre in track_genres:
                    if genre not in self.genres:
                        self.genres.append(genre)
        except:
            pass
