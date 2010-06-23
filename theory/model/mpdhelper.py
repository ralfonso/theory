import mpd
import logging
import random
import socket
import re

from pylons import app_globals as g
from theory.lib import helpers as h

log = logging.getLogger(__name__)


def wrap_error(fn):
    def new(*args, **kwargs):
        try:
            r = fn(*args, **kwargs)
        except mpd.ConnectionError:
            log.debug('connectionerror, attempt reconnect')
            args[0].connect()
            r = fn(*args, **kwargs)

        return r

    return new

class mpdhelper(object):
    """ 
    most python-mpd functions are handed off to python-mpd.  this class overwrites some of them
    to add required processing features (e.g. sorting) and also provides some convenience functions
    for common tasks
    """

    mpdc = None

    def __init__(self, g): 
        self.mpdc = None
        self.g = g
        self.callbacks = []
        self.callback_param = []

    def add_callback(self, func, *p):
        #log.debug('adding callback: %s %s' % (str(func), p))
        self.callbacks.append(func)
        self.callback_param.append(p)

    def connect(self):
        log.debug('Attempting to connect to %s:%s' % (self.g.tc.server, self.g.tc.port))
        self.mpdc = mpd.MPDClient()
        self.mpdc.connect(self.g.tc.server, self.g.tc.port)
        if self.g.tc.password:
            self.mpdc.password(self.g.tc.password)
            log.debug('using password')

        return self                

    def disconnect(self):
        log.debug('disconnect, calling callbacks on %s' % self)
        log.debug(self.callback_param)
        i = 0

        callbacks = self.callbacks
        param = self.callback_param

        self.callbacks = []
        self.callback_param = []

        for func in callbacks:
            #log.debug('callback: %s (%s)' % (str(func), param[i]))
            func(*(param[i]))


    @wrap_error
    def artists(self):
        artists = self.list('artist')
        artists.sort(self._sortartists)
        return artists

    @wrap_error
    def tracks(self,artist,album=None):
        # this is really ugly!

        if album:
            tracks = self.find('artist', artist, 'album', album)
            try:
                tracks.sort(self._sorttrackno)
            except (ValueError, KeyError):
                pass
        else:
            tracks = self.find('artist', artist)
            tracks.sort(self._sorttracktitle)

        trackno = 1

        for t in tracks:
            if 'album' not in t:
                t['album'] = ''
            h.format_title(t, trackno)
            trackno += 1

        return tracks

    @wrap_error
    def albums(self,artist):
        albums = self.list('album',artist)
        albums.sort(lambda x,y: cmp(x.lower(),y.lower()))
        return albums

    @wrap_error
    def get_random_tracks(self,incex,selected_genres,exclude_live,quantity):
        all_tracks = self.listallinfo()

        selected_tracks = []
        skipped_live = 0
        skipped_genre = 0
        skipped_not_file = 0

        log.debug("randomizer: total tracks %d" % len(all_tracks))

        for i in range(0,quantity):
            tracknum = len(all_tracks)

            if exclude_live:
                exc_re = re.compile('.*((\d{2}|\d{4})[-\/]\d{1,2}[-\/]\d{1,2}|\d{2}[-\/]\d{1,2}[-\/](\d{1,2}|\d{4}))')

            while True:
                # this loop keeps running until a valid track (based on the parameters) is found

                tracknum = len(all_tracks)
                try:
                    track = all_tracks.pop(random.randrange(tracknum))
                except (IndexError,ValueError):
                    track = None
                    break

                if 'file' in track:
                    if exclude_live:
                        if exc_re.match(track.get('album','')) or exc_re.match(track['file']):
                            skipped_live += 1
                            continue

                    track_genres = track.get('genre',None)
                    if track_genres: 
                        if type(track_genres) != list:
                            track_genres = [track_genres]
                       
                        if self._comparegenres(track_genres,selected_genres):
                            if incex == 'exclude':
                                continue
                        elif incex == 'include':
                            continue

                        break
                    else:
                        if incex == 'include':
                            continue
                        else:
                            break
                else:
                    skipped_not_file += 1

            if track is None:
                break

            selected_tracks.append(track)
               
        log.debug("randomizer: skipped live: %d / skipped genre: %d / skipped not file: %d" % (skipped_live,skipped_genre,skipped_not_file))
        log.debug("randomizer: sel: %d/%d left: %d" % (len(selected_tracks),quantity,len(all_tracks)))
        return selected_tracks


    def _comparegenres(self,tracklist,selectedlist):
        for t in tracklist:
            if t in selectedlist:
                return True

        return False

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
        if 'title' in x and 'title' in y:
            for track in (x,y):
                if type(track['title']) == list:
                    track['title'] = track['title'][0]

            return cmp(x['title'].lower(),y['title'].lower())
        else:
            return cmp(x['file'],y['file'])
            
    @wrap_error
    def __getattr__(self,attr):
        log.debug('getattr: %s' % attr)
        if self.mpdc is not None:
            try:
                return getattr(self.mpdc,attr)
            except socket.error, e:
                if isinstance(e.args, tuple):
                    log.debug("errno is %d" % e[0])
                    if e[0] == errno.EPIPE:
                       # remote peer disconnected
                       log.debug("Detected remote disconnect")
                    else:
                       # determine and handle different error
                       pass
                else:
                    print "socket error ", e

                log.debug('attempting reconnect')
                self = __init__(g)
            except mpd.ConnectionError,e:
                log.debug('attempting reconnect')
                self = __init__(g)
                self.connect()
                

        else:
            raise NoMPDConnection('Could not connect to the MPD server')
