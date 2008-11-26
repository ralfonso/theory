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
import socket
import random

from pylons import request, response, session
from pylons import tmpl_context as c
from pylons import app_globals as g
from pylons.controllers.util import abort, redirect_to
from pylons import config

from theory.lib.base import BaseController, render
from theory.lib import helpers as h
from theory.model.mpdpool import ConnectionClosed
from theory.model.albumart import AlbumArt,NoArtError
from theory.model.lyrics import *

from theory.model import *

log = logging.getLogger(__name__)

class MainController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/template.mako')
        # or, Return a response

        c.debug = request.GET.get('debug',0)
        
        try:
            g.p.connect()
        except ConnectionClosed:
            if g.tc.server is None:
                g.tc = TConfig()
                if g.tc.server is None:
                    c.config = '/config?firsttime=1'
            else:
                c.config = '/config?noconnection=1'
            pass

        return render('/index.html')

    def artists(self):
        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')

        c.artists = m.artists()
        return render('/artists.html')

    def albums(self):
        c.artist = request.GET.get('artist','')
        c.album = request.GET.get('album','')

        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')
        c.albums = m.albums(c.artist)

        aa = AlbumArt()
        c.album_imgs = aa.artist_art(c.artist)
        random.shuffle(c.album_imgs)
        return render('/albums.html')

    def tracks(self):
        c.artist = request.GET.get('artist','')
        c.album = request.GET.get('album','')
        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')


        c.tracks = m.tracks(c.artist,c.album)

   
        c.artist_safe = h.html.url_escape(c.artist)
        c.album_safe = h.html.url_escape(c.album.encode('utf-8'))

        return render('/tracks.html')
 
    def fetchart(self):
        artist = request.GET.get('artist','')
        album = request.GET.get('album','')
        response.headers['Content-type'] = 'image/jpg'

        try:
            aa = AlbumArt()
            aa.album_fetch(artist,album)
            img = aa.disk_path
        except NoArtError:
            response.headers['Content-type'] = 'image/png'
            img = 'theory/public/img/noart.png'


        f = open(img)
        data = f.read()
        f.close()

        return data
    
    def config(self,use_htmlfill=True):
        c.firsttime = request.GET.get('firsttime')
        c.noconnection = request.GET.get('noconnection')
        c.error = request.GET.get('error')
        c.type = request.GET.get('type')

        if use_htmlfill:
            return formencode.htmlfill.render(render("/config.html",{'server':g.tc.server,'port':g.tc.port,'awskey':g.tc.awskey}))
        else:
            return render("/config.html",{'server':g.tc.server,'port':g.tc.port,'awskey':g.tc.awskey})

    def saveconfig(self):
        try:
            fields = validate_custom(form.ConfigForm())
        except formencode.api.Invalid, e:
            return form.htmlfill(self.config(use_htmlfill=False),  e)

        if fields['action'] == 'save config':
            reloadframes = 'true'
            try:
                g.tc.update_config(fields['server'],fields['port'],fields['awskey'])
            except:
                redirect_to('/config?error=1&type=save')
        else:
            reloadframes = 'false'

        g.p.dispose()

        return '<script language="javascript">window.parent.hideConfig(%s)</script>' % reloadframes


    def lyrics(self):
        artist = request.GET.get('artist')
        track = request.GET.get('track')
    
        l = Lyrics(artist,track)
        c.lyrics = l.lyrics
        return render('/lyrics.html')

    def stats(self):
        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')

        c.stats = m.stats()
        aa = AlbumArt()
        c.dir_size = aa.dir_size()

        return render('/stats.html')
