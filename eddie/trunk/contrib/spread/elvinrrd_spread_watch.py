#!/usr/bin/env python
# encoding: utf-8
"""
elvinrrd_spread_watch.py

Created by Chris Miles on 2007-01-11.
Copyright (c) 2007 Chris Miles. All rights reserved.

For testing the receipt of elvinrrd messages over Spread.
Example:
  $ python elvinrrd_spread_watch.py -s localhost 
  Connecting to Spread server: localhost:4803
  
  Tue Jan 16 17:55:14 2007
  {'ELVINRRD': 'loadavg1-myhost',
   'loadavg1': '0.01',
   'timestamp': 1168970114.718941}
  
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
from datetime import datetime

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


def spread_watch(spread_host='127.0.0.1', spread_port=spread.DEFAULT_SPREAD_PORT):
    print "Connecting to Spread server: %s:%d" %(spread_host, spread_port)
    server = "%d@%s" % (spread_port, spread_host)
    s = spread.connect(server)
    s.join('elvinrrd')
    
    while True:
        m = s.receive()
        if m:
            print
            print time.ctime(time.time())
            if hasattr(m, 'message'):
                # RegularMsgType
                mio = StringIO(m.message)
                up = cPickle.Unpickler(mio)
                j = up.load()
                pprint(j)
                tstamp = j.get('timestamp', None)
                if tstamp:
                    print "  timestamp = %s" %str(datetime.fromtimestamp(tstamp))
            else:
                # MembershipMsgType
                print "* Membership change for group: %s" % m.group
                if m.reason == spread.CAUSED_BY_JOIN:
                    reason = "Members joined"
                elif m.reason == spread.CAUSED_BY_LEAVE:
                    reason = "Members left"
                elif m.reason == spread.CAUSED_BY_DISCONNECT:
                    reason = "Members disconnected"
                elif m.reason == spread.CAUSED_BY_NETWORK:
                    reason = "Members dropped (network problem?)"
                elif m.reason == 0:
                    reason = "transitional membership message: "
                else:
                    reason = "Unknown"
                
                print "  %s: %s" % (reason, ', '.join(m.extra))
                print "  Members in group now: ", ', '.join(m.members)
                


def main():
    '''Command-line entry point.
    '''
    
    # define usage and version messages
    usageMsg = "usage: %prog [options]"
    versionMsg = """elvinrrd_spread_watch.py %s""" % __version__
    
    # get a parser object and define our options
    parser = optparse.OptionParser(usage=usageMsg, version=versionMsg)
    parser.add_option('-s', '--server', dest='spread_host',
			metavar="HOSTNAME", help="Spread server HOSTNAME")
    parser.add_option('-p', '--port', dest='spread_port',
			metavar="PORT", help="Spread server PORT")
    parser.set_defaults(spread_host='127.0.0.1', spread_port=spread.DEFAULT_SPREAD_PORT)
    
    # Parse.  We dont accept arguments, so we complain if they're found.
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.error('No extra arguments should be given')
    
    spread_watch(options.spread_host, int(options.spread_port))


if __name__ == '__main__':
    main()
