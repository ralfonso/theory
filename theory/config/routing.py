"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False
    
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE

    map.connect('/',controller='main',action='index')
    map.connect('/artists',controller='main',action='artists')
    map.connect('/config',controller='main',action='config')
    map.connect('/saveconfig',controller='main',action='saveconfig')
    map.connect('/albums',controller='main',action='albums')
    map.connect('/stats',controller='main',action='stats')
    map.connect('/tracks',controller='main',action='tracks')
    map.connect('/fullscreen',controller='main',action='fullscreen')
    map.connect('/randomizer',controller='main',action='randomizer')
    map.connect('/add_random',controller='main',action='add_random')
    map.connect('/filesystem',controller='main',action='filesystem')
    map.connect('/search',controller='main',action='search')
    map.connect('/streams',controller='main',action='streams')
    map.connect('/savestream',controller='main',action='savestream')
    map.connect('/deletestream',controller='main',action='deletestream')
    map.connect('/playlist',controller='playlist',action='index')
    map.connect('/playlist/save',controller='playlist',action='save')
    map.connect('/playlist/load',controller='playlist',action='load')
    map.connect('/playlist/delete',controller='playlist',action='delete')
    map.connect('/fetchart',controller='main',action='fetchart')
    map.connect('/lyrics',controller='main',action='lyrics')
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')
    map.connect('/{controller}/{action}/{id}/{val}')

    return map
