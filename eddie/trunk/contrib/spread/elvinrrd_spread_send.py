#!/usr/bin/env python
# encoding: utf-8
"""
elvinrrd_spread_send.py

Created by Chris Miles on 2007-01-11.
Copyright (c) 2007 Chris Miles. All rights reserved.

For testing the sending of elvinrrd messages over Spread.
Example:
  $ python elvinrrd_spread_send.py -s localhost loadavg1-myhost loadavg1=0.01
"""

__version__ = '1.0'

# ---- Python Modules
import cPickle
from cStringIO import StringIO
import os
import platform
from pprint import pprint
import sys
import time

# optparse is only available in 2.3+, but optik provides the same 
# functionality for python 2.2
try:
    import optparse
except ImportError:
    try:
        import optik as optparse
    except ImportError:
        print "Error: requires Optik on Python 2.2.x (http://optik.sf.net)"
        sys.exit(1)

# ---- Spread Modules - http://www.python.org/other/spread/
import spread


def spread_send(elvinrrd, rrditems, spread_host='127.0.0.1', spread_port=spread.DEFAULT_SPREAD_PORT):
    msg = {
        'ELVINRRD'      : elvinrrd,
        'timestamp'     : time.time(),
    }
    msg.update(rrditems)
    
    print "Connecting to Spread server: %s:%d" %(spread_host, spread_port)
    server = "%d@%s" % (spread_port, spread_host)
    name = "test@%s" % (platform.node())
    s = spread.connect(server, name)
    #s.join('elvinrrd')    # don't need to join to send to group
    
    print "Sending message:"
    pprint(msg)
    
    sio = StringIO()
    p = cPickle.Pickler(sio)
    p.dump(msg)
    r = s.multicast(spread.RELIABLE_MESS, 'elvinrrd', sio.getvalue())
    
    if r > 0:
        print "message sent OK"
    else:
        print "message send failed"


def main():
    '''Command-line entry point.
    '''
    
    # define usage and version messages
    usageMsg = "usage: %prog [options] <ELVINRRD name> <key>=<value> ..."
    versionMsg = """elvinrrd_spread_send.py %s""" % __version__
    
    # get a parser object and define our options
    parser = optparse.OptionParser(usage=usageMsg, version=versionMsg)
    parser.add_option('-s', '--server', dest='spread_host',
			metavar="HOSTNAME", help="Spread server HOSTNAME")
    parser.add_option('-p', '--port', dest='spread_port',
			metavar="PORT", help="Spread server PORT")
    parser.set_defaults(spread_host='127.0.0.1', spread_port=spread.DEFAULT_SPREAD_PORT)
    
    # Parse.  We dont accept arguments, so we complain if they're found.
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error(usageMsg)
    
    elvinrrd = args[0]
    rrditems = {}
    for arg in args[1:]:
        (key, val) = arg.split('=', 1)
        rrditems[key] = val
    spread_send(elvinrrd, rrditems, options.spread_host, int(options.spread_port))


if __name__ == '__main__':
    main()
