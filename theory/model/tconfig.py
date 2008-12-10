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
from pylons import config
from pylons import app_globals as g

class ConfigFileError(Exception):
    pass

class TConfig:
    """
    handles the global configuration.  loaded into app globals at application startup
    also handles committing the configuration to disk to maintain across app restarts
    """

    server = None
    port = None
    password = None
    webpassword = None
    awskey = None

    def __init__(self):
        """ try to read the configuration from disk """

        conf = ConfigParser.ConfigParser()
     	conf.read(config['localconf'])
        try:
            self.server = conf.get('mpd','server')
            self.port = conf.get('mpd','port')
            self.awskey = conf.get('services','awskey')
            self.password = conf.get('mpd','password')
            self.webpassword = conf.get('main','webpassword')

        except (ConfigParser.NoSectionError,ConfigParser.NoOptionError):
            pass

    def update_config(self,server,port,password,webpassword,awskey): 
        """ commit the configuration to disk """

        conf = ConfigParser.ConfigParser()
        conf.add_section("mpd")
        conf.set("mpd", "server",server)
        conf.set("mpd", "port",port)
        conf.set("mpd", "password",password)
        conf.add_section("services")
        conf.set('services','awskey',awskey)
        conf.add_section('main')
        conf.set('main','webpassword',webpassword)

        print config['localconf']

        try:
            conffile = open(config['localconf'],"w")
            conf.write(conffile)
        except IOError,e:
            raise ConfigFileError

        self.server = server
        self.port = port
        self.password = password
        self.webpassword = webpassword
        self.awskey = awskey
