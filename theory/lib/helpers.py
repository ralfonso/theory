"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
# Import helpers as desired, or define your own, ie:
# from webhelpers.html.tags import checkbox, password

import datetime
from webhelpers import util,html
from webhelpers.html import tags

def format_time(seconds):
    try:
        seconds = int(seconds)
        hours = seconds / 60 / 60
        minutes = (seconds - hours * 60 * 60) / 60
        seconds = seconds - (hours * 60 * 60) - (minutes * 60)
        if hours:
            return "%d:%d:%02d" % (hours,minutes,seconds)
        else:
            return "%d:%02d" % (minutes,seconds)
    except TypeError:
        return '00:00'

def format_filesize(bytes):        
    kb = "%02.2fKB" % (bytes / 1024.0)
    return kb

def timestamp_to_friendly_date(ts):
    try:
        date = datetime.datetime.fromtimestamp(int(ts))
        return date.strftime("%Y-%m-%d %H:%M:%S")
    except TypeError:
        return 'unable to determine'

def format_title(t,trackno=None):
    try:
        t['formattedtrack'] = "%02d. %s" % (int(t['track']),t['title'])
    except KeyError,e:
        if t.has_key('title'):
            t['formattedtrack'] = "%s" % (t['title'])
    except ValueError,e:
        if t.has_key('title'):
            t['formattedtrack'] = "%s. %s" % (t['track'],t['title'])
        else:
            if t.has_key('title'):
                t['formattedtrack'] = "%s" % t['title']
    
    if not t.has_key('formattedtrack'):
        if trackno:
            t['formattedtrack'] = "%d." % trackno
        else:
            t['formattedtrack'] = '<unknown>'

def format_title_search(t):
    try:
        t['formattedtrack'] = "%s - %s - %s" % (t['artist'],t['album'],t['title'])
    except KeyError,e:
        if t.has_key('title'):
            t['formattedtrack'] = "%s" % (t['title'])
    
    if not t.has_key('formattedtrack'):
        t['formattedtrack'] = "%s" % t['file']
