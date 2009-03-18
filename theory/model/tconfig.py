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

import ConfigParser 
import pickle
from pylons import config
from pylons import app_globals as g

class ConfigFileError(Exception):
    pass

class TConfig:
    """
    handles the global configuration.  loaded into app globals at application startup
    also handles committing the configuration to disk to maintain across app restarts
    """

    def __init__(self):
        """ try to read the configuration from disk """
        self.server = None
        self.port = None
        self.password = None
        self.webpassword = ''
        self.timeout = False
        self.awskey = None
        self.streams = []
        self.default_search = 'Any'

        conf = ConfigParser.ConfigParser()
        conf.read(config['localconf'])

        try:
            self.server = conf.get('mpd','server')
            self.port = conf.get('mpd','port')
            self.awskey = conf.get('services','awskey')
            self.password = conf.get('mpd','password')
            self.webpassword = conf.get('main','webpassword')
            self.timeout = conf.getboolean('main','timeout')
            self.default_search = conf.get('main','default_search') 
            conf_stream = conf.get('ext','streams')
        except (ConfigParser.NoSectionError,ConfigParser.NoOptionError):
            pass

        try:
            self.streams = pickle.loads(eval(conf_stream))
        except:
            # we don't really care what happened, the user must have messed with the magic pickled string :)
            pass



    def commit_config(self):
        """ commit the configuration to disk """

        conf = ConfigParser.ConfigParser()
        conf.add_section("mpd")
        conf.set("mpd", "server",self.server)
        conf.set("mpd", "port",self.port)
        conf.set("mpd", "password",self.password)
        conf.add_section("services")
        conf.set('services','awskey',self.awskey)
        conf.add_section('main')
        conf.set('main','webpassword',self.webpassword)
        conf.set('main','timeout',self.timeout)
        conf.set('main','default_search',self.default_search)
        conf.add_section('ext')
        conf.set('ext','streams',repr(pickle.dumps(self.streams)))

        try:
            conffile = open(config['localconf'],"w")
            conf.write(conffile)
        except IOError,e:
            raise ConfigFileErro
                

    def get_stream_name(self,url):
        """ search the list of streams for a particular name """

        for s in self.streams:
            if s[1] == url:
                return s[0]
