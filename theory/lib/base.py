"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons.controllers.util import redirect
from pylons import url
from pylons import app_globals as g

from pylons import session

log = logging.getLogger(__name__)

class BaseController(WSGIController):
    requires_auth = False


    def __before__(self):
        self.m = None
        # Authentication required?
        if self.requires_auth and 'user' not in session and g.tc.webpassword != '':
            # Remember where we came from so that the user can be sent there
            # after a successful login
            return redirect(url(controller='login', action='login'))

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        return WSGIController.__call__(self, environ, start_response)

    def __after__(self):
        log.debug('after')
        if self.m:
            self.m.disconnect()
