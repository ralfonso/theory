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

import weakref, time
import logging
import socket

import theory.model.mpdqueue as Queue
from theory.model.mpdhelper import mpdhelper
from mpd import *

from theory.model.mpdutil import thread,threading


""" 
    this was mostly completely ripped off from SQLAlchemy's connection manager.  
    it has been modified to work (mostly) with the python-mpd connection objects.
"""


class ConnectionClosed(Exception):
    pass

class IncorrectPassword(Exception):
    pass

class Pool(object):
    """Base class for connection pools.

    This is an abstract class, implemented by various subclasses
    including:

    QueuePool
      Pools multiple connections using ``Queue.Queue``.

    SingletonThreadPool
      Stores a single connection per execution thread.

    NullPool
      Doesn't do any pooling; opens and closes connections.

    AssertionPool
      Stores only one connection, and asserts that only one connection
      is checked out at a time.

    The main argument, `creator`, is a callable function that returns
    a newly connected DB-API connection object.

    Options that are understood by Pool are:

    echo
      If set to True, connections being pulled and retrieved from/to
      the pool will be logged to the standard output, as well as pool
      sizing information.  Echoing can also be achieved by enabling
      logging for the "sqlalchemy.pool" namespace. Defaults to False.

    use_threadlocal
      If set to True, repeated calls to ``connect()`` within the same
      application thread will be guaranteed to return the same
      connection object, if one has already been retrieved from the
      pool and has not been returned yet. This allows code to retrieve
      a connection from the pool, and then while still holding on to
      that connection, to call other functions which also ask the pool
      for a connection of the same arguments; those functions will act
      upon the same connection that the calling method is using.
      Defaults to False.

    recycle
      If set to non -1, a number of seconds between connection
      recycling, which means upon checkout, if this timeout is
      surpassed the connection will be closed and replaced with a
      newly opened connection. Defaults to -1.

    listeners
      A list of ``PoolListener``-like objects or dictionaries of callables
      that receive events when DB-API connections are created, checked out and
      checked in to the pool.

    reset_on_return
      Defaults to True.  Reset the database state of connections returned to
      the pool.  This is typically a ROLLBACK to release locks and transaction
      resources.  Disable at your own peril.

    """
    def __init__(self, creator, recycle=-1, echo=None, use_threadlocal=False,
                 reset_on_return=True, listeners=None):
        #self.logger = log.instance_logger(self, echoflag=echo)
        self.logger = logging.getLogger(__name__)
        # the WeakValueDictionary works more nicely than a regular dict of
        # weakrefs.  the latter can pile up dead reference objects which don't
        # get cleaned out.  WVD adds from 1-6 method calls to a checkout
        # operation.
        self._threadconns = weakref.WeakValueDictionary()
        self._creator = creator
        self._recycle = recycle
        self._use_threadlocal = use_threadlocal
        self._reset_on_return = reset_on_return
        self.echo = echo
        self.listeners = []
        self._on_connect = []
        self._on_checkout = []
        self._on_checkin = []

        if listeners:
            for l in listeners:
                self.add_listener(l)

    def unique_connection(self):
        return _ConnectionFairy(self).checkout()

    def create_connection(self):
        return _ConnectionRecord(self)

    def recreate(self):
        """Return a new instance with identical creation arguments."""

        raise NotImplementedError()

    def dispose(self):
        """Dispose of this pool.

        This method leaves the possibility of checked-out connections
        remaining open, It is advised to not reuse the pool once dispose()
        is called, and to instead use a new pool constructed by the
        recreate() method.
        """

        raise NotImplementedError()

    def connect(self):
        if not self._use_threadlocal:
            return _ConnectionFairy(self).checkout()

        try:
            return self._threadconns[thread.get_ident()].checkout()
        except (KeyError,ConnectionClosed):
            agent = _ConnectionFairy(self)
            self._threadconns[thread.get_ident()] = agent
            return agent.checkout()

    def return_conn(self, record):
        if self._use_threadlocal and thread.get_ident() in self._threadconns:
            del self._threadconns[thread.get_ident()]
        self.do_return_conn(record)

    def get(self):
        return self.do_get()

    def do_get(self):
        raise NotImplementedError()

    def do_return_conn(self, conn):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def add_listener(self, listener):
        """Add a ``PoolListener``-like object to this pool.

        ``listener`` may be an object that implements some or all of
        PoolListener, or a dictionary of callables containing implementations
        of some or all of the named methods in PoolListener.

        """

        listener = as_interface(
            listener, methods=('connect', 'checkout', 'checkin'))

        self.listeners.append(listener)
        if hasattr(listener, 'connect'):
            self._on_connect.append(listener)
        if hasattr(listener, 'checkout'):
            self._on_checkout.append(listener)
        if hasattr(listener, 'checkin'):
            self._on_checkin.append(listener)

    def log(self, msg):
        self.logger.debug(msg)

class _ConnectionRecord(object):
    def __init__(self, pool):
        self.__pool = pool
        self.connection = self.__connect()
        self.info = {}
        if pool._on_connect:
            for l in pool._on_connect:
                l.connect(self.connection, self)

    def close(self):
        if self.connection is not None:
            if self.__pool._should_log_info:
                self.__pool.log("Closing connection %r" % self.connection)
            try:
                self.connection.close()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                if self.__pool._should_log_info:
                    self.__pool.log("Exception closing connection %r" %
                                    self.connection)

    def invalidate(self, e=None):
        if self.__pool._should_log_info:
            if e is not None:
                self.__pool.log("Invalidate connection %r (reason: %s:%s)" %
                                (self.connection, e.__class__.__name__, e))
            else:
                self.__pool.log("Invalidate connection %r" % self.connection)
        self.__close()
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = self.__connect()
            self.info.clear()
            if self.__pool._on_connect:
                for l in self.__pool._on_connect:
                    l.connect(self.connection, self)
        elif (self.__pool._recycle > -1 and time.time() - self.starttime > self.__pool._recycle):
            if self.__pool._should_log_info:
                self.__pool.log("Connection %r exceeded timeout; recycling" %
                                self.connection)
            self.__close()
            self.connection = self.__connect()
            self.info.clear()
            if self.__pool._on_connect:
                for l in self.__pool._on_connect:
                    l.connect(self.connection, self)
        return self.connection

    def __close(self):
        try:
            if self.__pool._should_log_info:
                self.__pool.log("Closing connection %r" % self.connection)
            self.connection.close()
        except Exception, e:
            if self.__pool._should_log_info:
                self.__pool.log("Connection %r threw an error on close: %s" %
                                (self.connection, e))
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise

    def __connect(self):
        try:
            self.starttime = time.time()
            connection = self.__pool._creator()
            if self.__pool._should_log_info:
                self.__pool.log("Created new connection %r" % connection)
            return connection
        except CommandError,e:
            if 'incorrect password' in e:
                raise IncorrectPassword
        except Exception, e:
            if self.__pool._should_log_info:
                self.__pool.log("Error on connect(): %s" % e)
            raise

    properties = property(lambda self: self.info,
                          doc="A synonym for .info, will be removed in 0.5.")

def _finalize_fairy(connection, connection_record, pool, ref=None):
    if ref is not None and connection_record.backref is not ref:
        return
    """
    if connection is not None:
        try:
            if pool._reset_on_return:
                connection.rollback()
            # Immediately close detached instances
            if connection_record is None:
                connection.close()
        except Exception, e:
            if connection_record is not None:
                connection_record.invalidate(e=e)
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise
    """
    if connection_record is not None:
        connection_record.backref = None
        if pool._should_log_info:
            pool.log("Connection %r being returned to pool" % connection)
        if pool._on_checkin:
            for l in pool._on_checkin:
                l.checkin(connection, connection_record)
        pool.return_conn(connection_record)

class _ConnectionFairy(object):
    """Proxies a DB-API connection and provides return-on-dereference support."""

    def __init__(self, pool):
        self._pool = pool
        self.__counter = 0
        try:
            rec = self._connection_record = pool.get()
            conn = self.connection = self._connection_record.get_connection()
            self._connection_record.backref = weakref.ref(self, lambda ref:_finalize_fairy(conn, rec, pool, ref))
        except:
            self.connection = None # helps with endless __getattr__ loops later on
            self._connection_record = None
            raise
        if self._pool._should_log_info:
            self._pool.log("Connection %r checked out from pool" %
                           self.connection)

    _logger = property(lambda self: self._pool.logger)

    is_valid = property(lambda self:self.connection is not None)

    def _get_info(self):
        """An info collection unique to this DB-API connection."""

        try:
            return self._connection_record.info
        except AttributeError:
            if self.connection is None:
                raise ConnectionError("This connection is closed")
            try:
                return self._detached_info
            except AttributeError:
                self._detached_info = value = {}
                return value
    info = property(_get_info)
    properties = property(_get_info)

    def invalidate(self, e=None):
        """Mark this connection as invalidated.

        The connection will be immediately closed.  The containing
        ConnectionRecord will create a new connection when next used.
        """

        if self.connection is None:
            raise ConnectionError("This connection is closed")
        if self._connection_record is not None:
            self._connection_record.invalidate(e=e)
        self.connection = None
        self._close()

    def __getattr__(self, key):
        return getattr(self.connection, key)

    def checkout(self):
        if self.connection is None:
            raise ConnectionClosed("This connection is closed")
        self.__counter += 1

        try:
            if not self._pool._on_checkout or self.__counter != 1:
                if self.connection.mpdc is not None:
                    self.connection.ping()
                else:
                    raise ConnectionError
                return self
        except (ConnectionError,AttributeError,socket.error):
            pass

        # Pool listeners can trigger a reconnection on checkout
        attempts = 2
        while attempts > 0:
            try:
                for l in self._pool._on_checkout:
                    l.checkout(self.connection, self._connection_record, self)

                if self.connection.mpdc is not None:
                    self.connection.ping()
                else:
                    raise ConnectionError
                return self
            except (ConnectionError, AttributeError,socket.error),e:
                if self._pool._should_log_info:
                    self._pool.log(
                    "Disconnection detected on checkout: %s" % e)
                self._connection_record.invalidate(e)
                self.connection = self._connection_record.get_connection()
                attempts -= 1

        if self._pool._should_log_info:
            self._pool.log("Reconnection attempts exhausted on checkout")
        self.invalidate()
        raise ConnectionClosed("This connection is closed")

    def detach(self):
        """Separate this connection from its Pool.

        This means that the connection will no longer be returned to the
        pool when closed, and will instead be literally closed.  The
        containing ConnectionRecord is separated from the DB-API connection,
        and will create a new connection when next used.

        Note that any overall connection limiting constraints imposed by a
        Pool implementation may be violated after a detach, as the detached
        connection is removed from the pool's knowledge and control.
        """

        if self._connection_record is not None:
            self._connection_record.connection = None
            self._connection_record.backref = None
            self._pool.do_return_conn(self._connection_record)
            self._detached_info = \
              self._connection_record.info.copy()
            self._connection_record = None

    def close(self):
        self.__counter -= 1
        if self.__counter == 0:
            self._close()

    def _close(self):
        _finalize_fairy(self.connection, self._connection_record, self._pool)
        self.connection = None
        self._connection_record = None


class SingletonThreadPool(Pool):
    """A Pool that maintains one connection per thread.

    Maintains one connection per each thread, never moving a connection to a
    thread other than the one which it was created in.

    This is used for SQLite, which both does not handle multithreading by
    default, and also requires a singleton connection if a :memory: database
    is being used.

    Options are the same as those of Pool, as well as:

    pool_size: 5
      The number of threads in which to maintain connections at once.
    """

    def __init__(self, creator, pool_size=5, **params):
        params['use_threadlocal'] = True
        Pool.__init__(self, creator, **params)
        self._conns = {}
        self.size = pool_size

    def recreate(self):
        self.log("Pool recreating")
        return SingletonThreadPool(self._creator, pool_size=self.size, recycle=self._recycle, echo=self._should_log_info, use_threadlocal=self._use_threadlocal, listeners=self.listeners)

    def dispose(self):
        """Dispose of this pool.

        this method leaves the possibility of checked-out connections
        remaining opened, so it is advised to not reuse the pool once
        dispose() is called, and to instead use a new pool constructed
        by the recreate() method.
        """

        for key, conn in self._conns.items():
            try:
                conn.close()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                # sqlite won't even let you close a conn from a thread
                # that didn't create it
                pass
            del self._conns[key]

    def dispose_local(self):
        try:
            del self._conns[thread.get_ident()]
        except KeyError:
            pass

    def cleanup(self):
        for key in self._conns.keys():
            try:
                del self._conns[key]
            except KeyError:
                pass
            if len(self._conns) <= self.size:
                return

    def status(self):
        return "SingletonThreadPool id:%d thread:%d size: %d" % (id(self), thread.get_ident(), len(self._conns))

    def do_return_conn(self, conn):
        pass

    def do_get(self):
        try:
            return self._conns[thread.get_ident()]
        except KeyError:
            c = self.create_connection()
            self._conns[thread.get_ident()] = c
            if len(self._conns) > self.size:
                self.cleanup()
            return c

class QueuePool(Pool):
    """A Pool that imposes a limit on the number of open connections.

    Arguments include all those used by the base Pool class, as well
    as:

    pool_size
      The size of the pool to be maintained. This is the largest
      number of connections that will be kept persistently in the
      pool. Note that the pool begins with no connections; once this
      number of connections is requested, that number of connections
      will remain. Defaults to 5.

    max_overflow
      The maximum overflow size of the pool. When the number of
      checked-out connections reaches the size set in pool_size,
      additional connections will be returned up to this limit. When
      those additional connections are returned to the pool, they are
      disconnected and discarded. It follows then that the total
      number of simultaneous connections the pool will allow is
      pool_size + `max_overflow`, and the total number of "sleeping"
      connections the pool will allow is pool_size. `max_overflow` can
      be set to -1 to indicate no overflow limit; no limit will be
      placed on the total number of concurrent connections. Defaults
      to 10.

    timeout
      The number of seconds to wait before giving up on returning a
      connection. Defaults to 30.
    """

    def __init__(self, creator, pool_size = 2, max_overflow = 10, timeout=30, **params):
        Pool.__init__(self, creator, **params)
        self._pool = Queue.Queue(pool_size)
        self._overflow = 0 - pool_size
        self._max_overflow = max_overflow
        self._timeout = timeout
        self._should_log_info = True
        self._overflow_lock = self._max_overflow > -1 and threading.Lock() or None

    def recreate(self):
        self.log("Pool recreating")
        return QueuePool(self._creator, pool_size=self._pool.maxsize, max_overflow=self._max_overflow, timeout=self._timeout, recycle=self._recycle, echo=self._should_log_info, use_threadlocal=self._use_threadlocal, listeners=self.listeners)

    def do_return_conn(self, conn):
        try:
            self._pool.put(conn, False)
        except Queue.Full:
            if self._overflow_lock is None:
                self._overflow -= 1
            else:
                self._overflow_lock.acquire()
                try:
                    self._overflow -= 1
                finally:
                    self._overflow_lock.release()

    def do_get(self):
        try:
            wait = self._max_overflow > -1 and self._overflow >= self._max_overflow
            return self._pool.get(wait, self._timeout)
        except Queue.Empty:
            if self._max_overflow > -1 and self._overflow >= self._max_overflow:
                if not wait:
                    return self.do_get()
                else:
                    #raise exc.TimeoutError("QueuePool limit of size %d overflow %d reached, connection timed out, timeout %d" % (self.size(), self.overflow(), self._timeout))
                    raise ConnectionError("QueuePool limit of size %d overflow %d reached, connection timed out, timeout %d. Please disable debugging and/or firebug." % (self.size(), self.overflow(), self._timeout))

            if self._overflow_lock is not None:
                self._overflow_lock.acquire()

            if self._max_overflow > -1 and self._overflow >= self._max_overflow:
                if self._overflow_lock is not None:
                    self._overflow_lock.release()
                return self.do_get()

            try:
                con = self.create_connection()
                self._overflow += 1
            finally:
                if self._overflow_lock is not None:
                    self._overflow_lock.release()
            return con

    def dispose(self):
        while True:
            try:
                conn = self._pool.get(False)
                conn.close()
            except Queue.Empty:
                break

        self._overflow = 0 - self.size()
        if self._should_log_info:
            self.log("Pool disposed. " + self.status())

    def status(self):
        tup = (self.size(), self.checkedin(), self.overflow(), self.checkedout())
        return "Pool size: %d  Connections in pool: %d Current Overflow: %d Current Checked out connections: %d" % tup

    def size(self):
        return self._pool.maxsize

    def checkedin(self):
        return self._pool.qsize()

    def overflow(self):
        return self._overflow

    def checkedout(self):
        return self._pool.maxsize - self._pool.qsize() + self._overflow

class NullPool(Pool):
    """A Pool which does not pool connections.

    Instead it literally opens and closes the underlying DB-API connection
    per each connection open/close.
    """

    def status(self):
        return "NullPool"

    def do_return_conn(self, conn):
        conn.close()

    def do_return_invalid(self, conn):
        pass

    def do_get(self):
        return self.create_connection()

class StaticPool(Pool):
    """A Pool of exactly one connection, used for all requests."""

    def __init__(self, creator, **params):
        Pool.__init__(self, creator, **params)
        self._conn = creator()
        self.connection = _ConnectionRecord(self)

    def status(self):
        return "StaticPool"

    def dispose(self):
        self._conn.close()
        self._conn = None
        
    def create_connection(self):
        return self._conn

    def do_return_conn(self, conn):
        pass

    def do_return_invalid(self, conn):
        pass

    def do_get(self):
        return self.connection


class AssertionPool(Pool):
    """A Pool that allows at most one checked out connection at any given time.

    This will raise an exception if more than one connection is checked out
    at a time.  Useful for debugging code that is using more connections
    than desired.
    """

    ## TODO: modify this to handle an arbitrary connection count.

    def __init__(self, creator, **params):
        Pool.__init__(self, creator, **params)
        self.connection = _ConnectionRecord(self)
        self._conn = self.connection

    def status(self):
        return "AssertionPool"

    def create_connection(self):
        raise "Invalid"

    def do_return_conn(self, conn):
        assert conn is self._conn and self.connection is None
        self.connection = conn

    def do_return_invalid(self, conn):
        raise "Invalid"

    def do_get(self):
        assert self.connection is not None
        c = self.connection
        self.connection = None
        return c
