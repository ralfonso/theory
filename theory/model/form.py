import formencode 
import pylons
from pylons import app_globals as g

class ConfigForm(formencode.Schema):
    allow_extra_fields = False
    filter_extra_fields = True

    action = formencode.validators.String(not_empty=False,if_missing=None)
    cancel = formencode.validators.String(not_empty=False,if_missing=None)
    server = formencode.validators.String(strip=True,not_empty=True,messages={'empty':'please enter a server host name'})
    port = formencode.validators.Int(strip=True,not_empty=True,messages={'empty':'please enter a port, MPD default is 6600',
                                                              'integer':'please enter an integer value for port, MPD default is 6600'
                                                             })
    password = formencode.validators.String(not_empty=False,if_missing=None)
    webpassword = formencode.validators.String(not_empty=False,if_missing=None)
    timeout = formencode.validators.Bool()
    awskey = formencode.validators.String(strip=True,not_empty=False,if_missing=None)

class StreamNameInUse(formencode.validators.FancyValidator):
    def validate_python(self, values, state):
        # if old name is set, don't do this check
        if values['oldname']:
            return

        if values['name'] in [name[0] for name in g.tc.streams]:
            raise formencode.Invalid({'stream_name_taken':"that stream name has already been used"}, values, state)


class StreamForm(formencode.Schema):
    allow_extra_fields = False
    
    name = formencode.validators.String(not_empty=True,strip=True,messages={'empty':'please enter a name for this stream'})
    url = formencode.validators.URL(not_empty=True,require_tld=False,strip=True,check_exists=False,messages={'empty':'please enter a URL'})
    oldname = formencode.validators.String(not_empty=False)

    chained_validators = [StreamNameInUse()]
                                                             

class State(object):
    """Trivial class to be used as State objects to transport information to formencode validators"""
    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])

    def __repr__(self):
        atts = []
        for key in self.__dict__:
            atts.append( (key, getattr(self, key)) )

        return self.__class__.__name__ + '(' + ', '.join(x[0] + '=' + repr(x[1]) for x in atts) + ')'

def validate_custom(schema, **state_kwargs):
    """Validate a formencode schema.
    Works similar to the @validate decorator. On success return a dictionary
    of parameters from request.params. On failure throws a formencode.Invalid
    exception."""
    # Create a state object if requested
    if state_kwargs:
        state = State(**state_kwargs)
    else:
        state = None

    # In case of validation errors an exception is thrown. This needs to
    # be caught elsewhere.
    return schema.to_python(pylons.request.params, state)

def htmlfill(html, exception_error=None):
    """Add formencode error messages to an HTML string.
    'html' contains the HTML page with the form (e.g. created with render()).
    'exception_error' is the formencode.Invalid-Exception from formencode."""

    return formencode.htmlfill.render(
        form=html,
        defaults=pylons.request.params,
        errors=(exception_error and exception_error.unpack_errors()),
        encoding=pylons.response.determine_charset()
    )
