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
import os
import logging
import re

from pylons import app_globals as g

class NoArtError(Exception):
    pass

class NoArtOnDisk(Exception):
    pass

class AlbumArt:
    amazonurl = None
    imgurl = None
    logger = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.www_root = '/img/art/'
        self.disk_root = 'theory/public/img/art/'

    def album_fetch(self,artist,album):
        """
        attempt to load an album's cover art from disk. 
        if it doesn't exist, make a request using Amazon's
        Web Services 
        """

        self.artist = artist
        self.album = album

        # some ID3 tags split a two-disc volume into two, attempt to remove that part of the tag for the search
        disc_num_found = re.search('(\(disc.+\)|\(CD.+\))',self.album,re.IGNORECASE)

        if disc_num_found:
            self.album = self.album[:disc_num_found.start()-1]

        self.set_file_paths()

        try:
            self.check_disk()
        except NoArtOnDisk:
            self.amazon_fetch()

    def artist_art(self,artist):
        """ return all of the album covers for a particular artist """

        images = []
        filenames = [filename for filename in os.listdir(self.disk_root) if filename.startswith("%s -" % artist)] 

        for i in filenames:
            album_name = i.split(' - ')[1][:-4]
            images.append({
                            'album'  :album_name,
                            'imgurl' :"%s/%s" % (self.www_root,i)
                         })
                            
        return images 

    def log(self,msg):
        self.logger.info(msg)

    def amazon_fetch(self):
        """ 
        attempts to fetch album cover art from Amazon Web Services and 
        calls save_to_disk() to save the largest available image permanently
        to avoid subsequent lookups
        """

        if g.tc.awskey == '':
            raise NoArtError

      
        artist_safe = urllib2.quote(self.artist)
        album_safe = urllib2.quote(self.album)

        try:
            url = 'http://ecs.amazonaws.com/onca/xml?Service=AWSECommerceService&AWSAccessKeyId=%s&Operation=ItemSearch&SearchIndex=Music&Version=2008-11-15&ResponseGroup=Images&Artist=%s&Title=%s' % (g.tc.awskey,artist_safe,album_safe)
            self.log('Fetching Amazon album image: %s' % url)
            urlfile = urllib2.urlopen(url)
        except urllib2.URLError:
            self.log('Error fetching Amazon XML')
            raise NoArtError

        doc = xml.dom.minidom.parse(urlfile)
        urlfile.close()
        imgnodes = doc.getElementsByTagName('LargeImage')

        if len(imgnodes) > 0:
            node = imgnodes[0]
            self.amazonurl =  node.firstChild.firstChild.nodeValue
            self.log('Found album art: %s' % self.amazonurl)
        else:
            raise NoArtError

        self.save_to_disk()

    def set_file_paths(self):
        """ set up the local paths images on both disk and web root """

        artist_pathsafe = self.artist.replace(os.sep,' ')
        album_pathsafe = self.album.replace(os.sep,' ')
        filename = "%s - %s.jpg" % (artist_pathsafe,album_pathsafe)
        self.www_path = os.path.join(self.www_root,filename)
        self.disk_path = os.path.join(self.disk_root,filename)

    def check_disk(self):
        """ check if cover art exists locally """

        if os.path.exists(self.disk_path):
            self.imgurl = self.www_path
        else:
            raise NoArtOnDisk

    def save_to_disk(self):
        """ save the fetched cover image to disk permanently """
        try:
            urlfile = urllib2.urlopen(self.amazonurl)
        except urllib2.URLError:
            raise NoArtError

        f = open(self.disk_path,'wb')
        f.write(urlfile.read())
        f.close()
        self.imgurl = self.www_path

    def dir_size(self):
        """ return the sum of the cover art disk usage """
        dir_size = 0

        for (path,dirs,files) in os.walk(self.disk_root):
            for file in files:
                filename = os.path.join(path,file)
                dir_size += os.path.getsize(filename)        

        return dir_size
