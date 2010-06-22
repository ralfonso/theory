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

import threading
from theory.model.mpdhelper import *

def threadsafe_function(fn):
    """decorator making sure that the decorated function is thread safe"""
    lock = threading.Lock()
    def new(*args, **kwargs):
        lock.acquire()
        try:
            r = fn(*args, **kwargs)
        except Exception as e:
            log.debug('threadsafe exception: %s' % e)
            raise NoMPDConnection
        finally:
            lock.release()
        return r
    return new

class NoMPDConnection(Exception):
    pass

class MPDPool:
    max_connections = 3
    max_overflow = 2

    in_use = {}
    connections = {}

    overflow_connections = {}
    overflow_in_use = {}

    def __init__(self, g):
        self.factory = mpdhelper
        self.g = g

    @threadsafe_function
    def recreate(self):
        for conn in self.connections:
            try:
                self.connections[conn].disconnect()
            except NoMPDConnection:
                pass

        for conn in self.overflow_connections:
            try:
                self.overflow_connections[conn].disconnect()
            except NoMPDConnection:
                pass

        self.in_use = {}
        self.overflow_in_use = {}

    @threadsafe_function
    def connect(self):
        log.debug('connections: %s, in_use: %s' % (self.connections, self.in_use))
        for id, instance in self.connections.items():
            if id in self.in_use:
                log.debug('id %d in use' % id)
                continue
            return self.got_conn(instance, id)

        # no free ones, create a new one
        log.debug('creating a new connection')
        for id in range(self.max_connections):
            log.debug('checking id: %d' % id)
            if id in self.connections:
                continue
            else:
                log.debug('new connection id: %d' % id)
                mpdc = self.factory(self.g)
                d = mpdc.connect()
                return self.got_conn(d, id)

        # max connections, check overflow

        for id, instance in self.overflow_connections.items():
            if id in self.overflow_in_use:
                log.debug('overflow id %d in use' % id)
                continue
            return self.got_conn(instance, id, overflow=True)

        for id in range(self.max_overflow):
            if id in self.overflow_connections:
                continue
            else:
                log.debug('new overflow connection id: %d' % id)
                mpdc = self.factory(self.g)
                d = mpdc.connect()
                return self.got_conn(d, id, overflow=True)

        raise MaxConnections                

    def __getattr__(self, attr):
        return getattr(self.mpdc, attr)

    def got_conn(self, obj, id, overflow=False):
        log.debug('marking id: %d in use' % id)
        if not overflow:
            self.connections[id] = obj
            self.in_use[id] = True
        else:            
            self.overflow_connections[id] = obj
            self.overflow_in_use[id] = True
       
        obj.add_callback(self.disconnect, id, overflow)

        print self.in_use
        i = sum(filter(lambda x:  x, self.in_use.values()))
        log.debug('%d in %d used' % (i, self.max_connections))
        return obj

    def disconnect(self, id, overflow):
        log.debug('disconnect')
        del self.in_use[id]
        log.debug('connections: %s, in_use: %s' % (self.connections, self.in_use))

class ConnectionClosed(Exception):
    pass
class ProtocolError(Exception):
    pass
class IncorrectPassword(Exception):
    pass
class MaxConenctions(Exception):
    pass
