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

from pylons import request, response, session
from pylons import tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as g

from theory.model.mpdpool import ConnectionClosed
from theory.lib.base import BaseController, render
#import theory.model as model

log = logging.getLogger(__name__)

class PlaylistController(BaseController):
    def index(self):
        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')

        status = m.status()
        c.playlistid = status['playlist']
        c.playlist = m.playlistinfo()
        info = m.lsinfo()
        c.available_playlists = [playlist['playlist'] for playlist in info if playlist.has_key('playlist')]
        c.available_playlists.insert(0,'')

        return render('/playlist.html')
 

    def save(self):
        name = request.GET.get('name',0)

        if name == 0:
            return ''

        m = g.p.connect()
        info = m.lsinfo()
        available_playlists = [playlist['playlist'] for playlist in info if playlist.has_key('playlist')]

        if name in available_playlists:
            m.rm(name)
        m.save(name)
        return 'saved!'

    def load(self):
        name = request.GET.get('name',0)
        if name == 0:
            return ''

        m = g.p.connect()
        m.load(name)
        return 'loaded!'

    def delete(self):
        name = request.GET.get('name',0)
        if name == 0:
            return ''

        m = g.p.connect()
        m.rm(name)
        return 'deleted!'
