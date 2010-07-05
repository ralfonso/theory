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
from pylons.controllers.util import abort
from pylons import app_globals as g

from theory.lib.base import BaseController, render
from theory.model.mpdpool import NoMPDConnection
#import theory.model as model

log = logging.getLogger(__name__)

class PlaylistController(BaseController):
    requires_auth = True

    def index(self):
        """ controller for the playlist frame """

        try:
            self.m = g.p.connect()
        except NoMPDConnection:            
            return render('/null.html')
        status = self.m.status()
        c.playlistid = status['playlist']
        c.playlist = self.m.playlistinfo()
        info = self.m.lsinfo()
        c.available_playlists = [playlist['playlist'] for playlist in info if 'playlist' in playlist]
        c.available_playlists.insert(0,'')
        c.g = g

        return render('/playlist.html')
 

    def save(self):
        """ commit a stored playlist to disk via MPD """
        name = request.GET.get('name',0)

        if name == 0:
            return ''

        self.m = g.p.connect()
        info = self.m.lsinfo()
        available_playlists = [playlist['playlist'] for playlist in info if 'playlist' in playlist]

        if name in available_playlists:
            self.m.rm(name)
        self.m.save(name)
        return 'saved!'

    def load(self):
        """ load a stored playlist into the running playlist """

        name = request.GET.get('name',0)
        if name == 0:
            return ''

        self.m = g.p.connect()
        self.m.load(name)
        return 'loaded!'

    def delete(self):
        """ delete a stored playlist from disk """

        name = request.GET.get('name',0)
        if name == 0:
            return ''

        self.m = g.p.connect()
        self.m.rm(name)
        return 'deleted!'
