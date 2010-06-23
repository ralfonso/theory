# theory MPD client
# Copyright (C) 2008  Ryan Roemmich <ralfonso@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import mpd

from pylons import request, response, session
from pylons import tmpl_context as c
from pylons import app_globals as g
from pylons.controllers.util import abort
from routes.util import redirect_to
from pylons.decorators import jsonify

from mpd import CommandError

from theory.lib.base import BaseController, render

log = logging.getLogger(__name__)

class MpdcontrolController(BaseController):
    requires_auth = True

    @jsonify
    def status(self):
        """ 
        this is the status data that the main indexes calls on an interval.
        uses the pylons @jsonify decorator to turn the output into something
        that can be parsed by JQuery's getJSON() function
        """
            
        self.m = g.p.connect()
        current = self.m.currentsong()
        status = self.m.status()
        #m.close()

        return dict(track=current,status=status)

    @jsonify
    def fs_status(self):
        """ 
        similar to status() but includes a forward-looking playlist 
        for the fullscreen widget
        """

        try:
            self.m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')

        status = self.m.status()
        current = self.m.currentsong()
        playlist = self.m.playlistinfo()

        track = 0
        found_current = False
        remaining_playlist = []

        for pl in playlist:
            if found_current:
                remaining_playlist.append(pl)

            if 'id' in current:
                if pl['id'] == current['id']:
                    found_current = True
           
            track += 1

        #m.close()
        return dict(status=status,current=current,playlist=remaining_playlist)

    def setvolume(self,id):
        self.m = g.p.connect()

        try:
            volume = id
            self.m.setvol(volume)
        except ValueError:
            pass

        #m.close()

    def seek(self,id,val):
        self.m = g.p.connect()
        try:
            id = id
            pos = val
            self.m.seekid(id,pos)
        except ValueError:
            pass

    def stop(self):
        self.m = g.p.connect()
        self.m.stop()
    
    def previous(self):
        self.m = g.p.connect()
        self.m.previous()
    
    def next(self):
        self.m = g.p.connect()
        self.m.next()

    def play(self):
        self.m = g.p.connect()
        status = self.m.status()
        if status['state'] == 'play':
            self.m.pause()
        else:
            self.m.play()

    def pause(self):
        self.m = g.p.connect()
        self.m.pause()

    def reorderplaylist(self):
        tracklist = request.POST.getall('track[]')
        self.m = g.p.connect()

        iter = 0

        for t in tracklist:
            parts = t.split(':')
            if iter != parts[1]:
                self.m.moveid(parts[0],iter)
                
            iter += 1

    def addtoplaylist(self):
        file = request.POST.get('file').encode('utf-8')

        self.m = g.p.connect()
        self.m.add(file)

    def addalbumtoplaylist(self):
        artist = request.GET.get('artist').encode('utf-8')
        album = request.GET.get('album').encode('utf-8')

        self.m = g.p.connect()
        tracks = self.m.tracks(artist,album)

        self.m.command_list_ok_begin()
        for t in tracks:
            self.m.add(t['file'])

        self.m.command_list_end()

    def addartistalbums(self):
        artist = request.GET.get('artist').encode('utf-8')

        self.m = g.p.connect()
        albums = self.m.albums(artist)

        tracklist = []

        for album in albums:
            tracklist.extend(self.m.tracks(artist,album))
        
        self.m.command_list_ok_begin()

        for t in tracklist:
            self.m.add(t['file'])

        self.m.command_list_end()


    def addpathtoplaylist(self):
        path = request.POST.get('path').encode('utf-8')

        self.m = g.p.connect()

        tracklist = []

        lsinfo = self.m.lsinfo(path)

        for f in lsinfo:
            if 'file' in f:
                tracklist.append(f)
        
        self.m.command_list_ok_begin()

        for t in tracklist:
            self.m.add(t['file'])

        self.m.command_list_end()  

    def removetrack(self,id):
        self.m = g.p.connect()
        try:
            self.m.deleteid(id)
        except CommandError,e: # exception if the track to be removed doesn't exist
            return str(e)
        finally:
            pass

    def removemultipletracks(self,id):
        self.m = g.p.connect()
        for id in id.split(','):
            if id:
                try:
                    self.m.deleteid(id)
                except CommandError,e: # exception if the track to be removed doesn't exist
                    pass

    def playnow(self,id):
        self.m = g.p.connect()
        try:
            self.m.playid(id)
            self.m.play()
        except CommandError,e:
            return str(e)
        finally:
            pass

    def repeat(self,id):
        self.m = g.p.connect()
        self.m.repeat(id)

    def random(self,id):
        self.m = g.p.connect()
        self.m.random(id)

    def rescan(self):
        self.m = g.p.connect()
        self.m.update()

    def clearplaylist(self):
        self.m = g.p.connect()
        self.m.clear()
        
    def shuffle(self):
        self.m = g.p.connect()
        self.m.shuffle()
        
    def trimplaylist(self):
        """ trims the playlist of everything leading up to the currently playing track """
        self.m = g.p.connect()
        current = self.m.status()
        playlist = self.m.playlistinfo()

        if not 'songid' in current:
            return

        if len(playlist) == 0:
            return

        self.m.command_list_ok_begin()

        for t in playlist:
            if current['songid'] != t['id']:
                self.removetrack(t['id'])
            else:
                break

        self.m.command_list_end()

    def playnext(self,id):
        self.m = g.p.connect()
        current = self.m.currentsong()
        if not 'pos' in current:
            return
        self.m.moveid(id,int(current['pos'])+1)

