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

import urllib2
import xml.dom.minidom
import logging

class NoLyricsError(Exception):
    pass

class Lyrics:
    artist = None
    track = None
    lyrics = None

    def __init__(self,artist,track):
        self.logger = logging.getLogger(__name__)
        self.artist = artist
        self.track = track

        artist_safe = urllib2.quote(self.artist)
        track_safe = urllib2.quote(self.track)

        try:
            url = 'http://lyricwiki.org/api.php?func=getSong&artist=%s&song=%s&fmt=xml' % (artist_safe,track_safe)
            self.log('Fetching lyrics: %s' % url)
            urlfile = urllib2.urlopen(url)
        except urllib2.URLError:
            self.log('Error fetching lyrics')
            raise NoLyricsError


        doc = xml.dom.minidom.parse(urlfile)
        urlfile.close()
        tag = doc.getElementsByTagName('lyrics')

        if len(tag) > 0:
            self.lyrics = tag[0].firstChild.nodeValue

    def log(self,msg):
        self.logger.info(msg)
