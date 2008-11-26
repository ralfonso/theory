"""The application's Globals object"""

from theory.model.mpdhelper import *
from theory.model.mpdpool import QueuePool
from theory.model.tconfig import TConfig

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """
    def get_mpd_conn(self):
        m = mpdhelper()
        return m

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable
        """

        self.p = QueuePool(self.get_mpd_conn, max_overflow=10, pool_size=5, use_threadlocal=True)
        self.tc = TConfig()
        pass



