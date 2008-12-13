import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import app_globals as g

from theory.lib.base import BaseController, render
#from theory import model

log = logging.getLogger(__name__)

class LoginController(BaseController):
   def login(self):
       """
       Show login form. Submits to /login/submit
       """

       return render('/login.html')

   def submit(self):
       """
       Verify password
       """
       form_password = str(request.params.get('password'))

       if form_password != g.tc.webpassword:
           c.err = 1
           return render('/login.html')

       # Mark user as logged in
       session['user'] = 'theory'
       session.save()

       redirect_to(controller='main')

   def logout(self):
       if 'user' in session:
           del session['user']
           session.save()

       redirect_to(controller='main')
