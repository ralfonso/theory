import mpd
from pylons import app_globals as g
import socket

class NoMPDConnection(Exception):
    pass

class mpdhelper(object):
    """ 
    most python-mpd functions are handed right off.  this class overloads some of them
    to add required processing features (e.g. sorting) and also provides some convenience functions
    for common tasks
    """

    mpdc = None

    def __init__(self): 
        try:
            self.mpdc = mpd.MPDClient()
            self.mpdc.connect(g.tc.server,g.tc.port)
        except (socket.gaierror,socket.error):
            self.mpdc = None

    def artists(self):
        artists = self.list('artist')
        artists.sort(self._sortartists)
        return artists

    def tracks(self,artist,album=None):
        # this is really ugly!


        if album:
            tracks = self.find('artist',artist,'album',album)
            try:
                tracks.sort(self._sorttrackno)
            except (ValueError,KeyError):
                pass
        else:
            tracks = self.find('artist',artist)
            tracks.sort(self._sorttracktitle)

        trackno = 1

        for t in tracks:
            try:
                t['formattedtrack'] = "%02d. %s" % (int(t['track']),t['title'])
            except KeyError,e:
                if t.has_key('title'):
                    t['formattedtrack'] = "%s" % (t['title'])
            except ValueError,e:
                if t.has_key('title'):
                    t['formattedtrack'] = "%s. %s" % (t['track'],t['title'])
                else:
                    if t.has_key('title'):
                        t['formattedtrack'] = "%s" % t['title']
            
            if not t.has_key('formattedtrack'):
                t['formattedtrack'] = "%d." % trackno
            trackno += 1

        return tracks

    def albums(self,artist):
        albums = self.list('album',artist)
        albums.sort(lambda x,y: cmp(x.lower(),y.lower()))
        return albums

    def _sorttrackno(self,x,y):
        xt = x['track']
        yt = y['track']

        if '/' in xt:
            xt = xt.split('/')[0]

        if '/' in yt:
            yt = yt.split('/')[0]

        return cmp(int(xt),int(yt))

    def _sortartists(self,x,y):
        x = x.lower()
        y = y.lower()

        if x[:4] == 'the ': x = x[4:]
        if y[:4] == 'the ': y = y[4:]

        return cmp(x,y)

    def _sorttracktitle(self,x,y):
        if x.has_key('title') and y.has_key('title'):   
            return cmp(x['title'].lower(),y['title'].lower())
        else:
            return cmp(x['file'],y['file'])
            

    def __getattr__(self,attr):
        if self.mpdc is not None:
            return getattr(self.mpdc,attr)
        else:
            raise NoMPDConnection('Could not connect to the MPD server')
