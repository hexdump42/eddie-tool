#! /usr/bin/env python
## 
## File         : elvinrrd.py
## Author       : Chris Miles <chris@psychofx.com>
## Start Date   : 20010827
## Description  : Elvin4 consumer to insert data sent via Elvin into RRDtool databases.
##
## $Id$
##

################################################################

__version__ = """2.2"""

################################################################

# Python modules
import sys
import traceback
import re
import string
import os
import getopt
import time

# Other modules
#import RRDtool	# requires PyRRDtool from http://freshmeat.net/projects/pyrrdtool/
import rrdtool	# requires py-rrdtool from http://sourceforge.net/projects/py-rrdtool/
		#                       or http://www.nongnu.org/py-rrdtool/
import elvin	# requires Elvin4 modules from http://elvin.dstc.edu.au/projects/pe4/index.html

# Default Elvin URL and SCOPE
ELVIN_URL='elvin://localhost'
ELVIN_SCOPE='elvin'

################################################################

class RRDstore:
    """
    Object with details of what to match in the Elvin message and
    how to store the data in RRD.
    """

    def __init__(self, elvinrrd, rrdfile, store, create):
	self.elvinrrd = elvinrrd
	self.rrdfile = rrdfile
	self.store = store
	self.create = create

	self.regexp = None
	if '*' in self.elvinrrd:	# if a wildcard, create a reg-exp
	    self.regexp = string.replace( self.elvinrrd, '*', "(.*)" )

	if debug:
	    log( "Created RRDstore object %s" % (self) )


    def __str__(self):
	return "[elvinrrd=%s rrdfile=%s store=%s create=%s]" % (self.elvinrrd, self.rrdfile, self.store, self.create)


class BaseElvin:
    """
    Base Elvin class to handle opening and closing Elvin connections.
    This should be sub-classed and consumer and/or producer functionality
    added.
    """

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	"""
	Initialise connection to Elvin server, using (in order of preference):
	- An Elvin server URL specified by elvinurl;
	- An Elvin scope specified by elvinscope;
	- Auto discovery if the above not set.
	"""

	self.elvinurl = elvinurl
	self.elvinscope = elvinscope

	if self.elvinurl and len(self.elvinurl) > 0:
	    connect_string=self.elvinurl
	elif self.elvinscope and len(self.elvinscope) > 0:
	    connect_string=self.elvinscope
	else:
	    connect_string='*'		# auto discovery

	if verbose:
	    log( "Trying Elvin connection to %s" % (connect_string) )

	try:
	    self.elvinc = elvin.connect( connect_string )
	    if verbose:
		log( "Elvin connection succeeded to %s" % (connect_string) )
	except:
	    sys.stderr.write( "Connection to elvin failed - connection string was '%s'\n" % (connect_string) )
	    if logfile != None:
		log( "Connection to elvin failed - connection string was '%s'" % (connect_string) )
	    sys.exit(1)


    def cleanExit(self):
	"""
	Close the Elvin connection cleanly.
	"""

	self.elvinc.close()	# close Elvin connection


class storeconsumer(BaseElvin):
    """
    An Elvin consumer to receive "ELVINRRD" messages from the Elvin network.
    """

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	apply( BaseElvin.__init__, (self, elvinurl, elvinscope) )


    def register(self):
	"""
	Subscribe for Elvin messages containing the key "ELVINRRD".
	"""

	self.subscription = 'require(ELVINRRD)'

	sub = self.elvinc.subscribe(self.subscription)
	sub.add_listener(self.deliver)
	sub.register()


    def deliver(self, sub, msg, insec, rock):
	"""
	This method handles any received "ELVINRRD" messages.
	It parses a valid message and stores the information in the appropriate
	RRD database, as defined by the elvinrrd configuration.

	Returns 0 if successful;
	Returns 1 if there were any problems.
	"""
 
	r = None
	inx = None
	try:
	    r = self.rrddict[msg[u'ELVINRRD']]
	except KeyError:
	    # no direct match, try to match wildcard entries
	    for x in self.rrddict.keys():
		inx = re.match( self.rrddict[x].regexp, msg[u'ELVINRRD'] )
		if inx:
		    r = self.rrddict[x]
		    break

	if r == None:
	    log( "warning: No match for message %s" % (msg) )
	    return 1

	rrdfile = r.rrdfile
	store = r.store
	create = r.create

	if inx:
	    # wildcard match - substitute in other variables as appropriate
	    if '*' in r.rrdfile:
	        rrdfile = str(string.replace( r.rrdfile, '*', inx.group(1) ))	# replace all '*' with first string from match
	    if '*' in r.store:
	        store = str(string.replace( r.store, '*', inx.group(1) ))	# replace all '*' with first string from match
	    if '*' in r.create:
	        create = str(string.replace( r.create, '*', inx.group(1) ))	# replace all '*' with first string from match

	if len(store) == 1:
	    # only one variable to store, use default method
	    try:
		val = msg[u'%s'%(store[0])]
	    except KeyError, err:
		log( "KeyError: %s, message %s" % (err, msg) )
		return 1

	    u = (rrdfile, "N:%s" % (str(val)))

	else:
	    # multiple variables to store - must name them
	    ds = "-t"
	    n = "N:"
	    for s in store:
		try:
		    val = msg[u'%s'%(s)]
		except KeyError, err:
		    log( "KeyError: %s, message %s" % (err, msg) )
		    return 1
		ds = "%s%s:" % (ds,s)
		n = "%s%s:" % (n,str(val))

	    ds = ds[:-1]    # remove ':' from end
	    n = n[:-1]      # remove ':' from end
	    u = (rrdfile, ds, n)

	if debug:
	    log( 'rrd.update( %s )' % (u,) )
	    #log( 'rrd.update( %s, %s, %s )' % (rrdfile, ds, n) )

	try:
	    #self.rrd.update( u )
	    self.rrd.update( *u )
	    #self.rrd.update( rrdfile, ds, n )
	#except IOError, err:
	except rrdtool.error, err:
	    if str(err).find('No such file or directory') != -1:
		if os.path.exists( rrdfile ):
		    # file exists, despite the error...
		    sys.stderr.write( "IOError: %s, message %s\n" % (err, msg) )
		    if logfile:
			log( "IOError: %s, message %s" % (err, msg) )
		else:
		    rrd_dir = os.path.dirname( rrdfile )

		    if not os.path.exists( rrd_dir ):
			if verbose:
			    log( "Creating directory '%s'" % (rrd_dir) )
			os.makedirs( rrd_dir )

		    createargs = (rrdfile,) + tuple(create.split())
		    if verbose:
			log( "Creating rrd: %s" % (createargs,) )
		    self.rrd.create( *createargs )
		    self.rrd.update( *u )
	    else:
		sys.stderr.write( "IOError: %s, message %s\n" % (err, msg) )
		if logfile:
		    log( "IOError: %s, message %s" % (err, msg) )

	return 0


def ReadConfig( filename ):
    """
    Read the configuration from the given filename.
    """

    if verbose:
	log( "Reading config from '%s'" % (filename) )

    rrddict = {}

    try:
        fp = open(filename, 'r')
    except IOError:
        sys.stderr.write( "Cannot open configuration file '%s', exiting" % (filename) )
	if logfile:
	    log( "Cannot open configuration file '%s', exiting" % (filename) )
	sys.exit(1)

    re_comment = "^\s*#.*$"
    re_empty = "^\s*$"
    re_line = "^\s*(.+)=(.+?)$"

    sre_comment = re.compile(re_comment)
    sre_empty = re.compile(re_empty)
    sre_line = re.compile(re_line)

    line = fp.readline()
    entry = 0	# not processing an entry yet
    elvinrrd = None
    rrdfile = None
    store = None
    create = None
    while len(line) > 0:
        if sre_comment.match(line) or sre_empty.match(line):
	    # commented or empty lines are ignored
	    # if we were processing an entry, store that entry
	    if entry == 1:
		# create new store object
		rrdobj = RRDstore( elvinrrd, rrdfile, store, create )
		rrddict[elvinrrd] = rrdobj
		entry = 0
	        elvinrrd = None
	        rrdfile = None
	        store = None
	        create = None
        else:
            inx = sre_line.match(line)
	    if inx == None:
	        print "Parse error, invalid line follows:\n%s" % (line)
	        sys.exit(1)
            else:
		entry = 1	# we are processing an entry
		if inx.group(1) == 'elvinrrd':
		    elvinrrd = inx.group(2)
		elif inx.group(1) == 'rrdfile':
		    rrdfile = inx.group(2)
		elif inx.group(1) == 'store':
		    store = inx.group(2)
		    if ',' in store:		# list of multiple store keys
			store = string.split(store, ',')
		    else:
			store = [store,]
		elif inx.group(1) == 'create':
		    create = inx.group(2)
		else:
		    sys.stderr.write( "Parse error, unknown keyword '%s' on following line:\n%s" % (inx.group(1),line) )
		    if logfile:
			log( "Parse error, unknown keyword '%s' on following line:\n%s" % (inx.group(1),line) )
		    sys.exit(1)

        line = fp.readline()

    if entry == 1:
	# create new store object
	rrdobj = RRDstore( elvinrrd, rrdfile, store, create )
	rrddict[elvinrrd] = rrdobj

    fp.close()

    if verbose:
	log( "%s parsed, %d entries in config" % (filename,len(rrddict.keys())) )

    return rrddict


def log( text ):
    """
    Log text to either logfile (if defined) or stdout.
    """

    if logfile != None:
	try:
	    fp = open(logfile, 'a')
	except IOError, err:
	    sys.stderr.write( "error: IOError opening '%s', %s\n" % (logfile, err) )
	    sys.exit(1)
	t = "%04d-%02d-%02d %02d:%02d:%02d" % (time.localtime()[0:6])
	fp.write( "%s %s\n" % (t, text) )
	fp.close()

    else:
	sys.stdout.write( "%s\n" % (text) )


def main():
    usage_short = "[-dhv] -c elvinrrd.cf [-e elvin_url] [-s elvin_scope] [-l logfile]"
    usage_long = "[--debug] [--help] [--verbose] --configfile elvinrrd.cf [--elvinurl elvin_url] [--elvinscope elvin_scope] [--logfile logfile]"
    usage = "usage: %s %s\n   or: %s" % (sys.argv[0], usage_short, usage_long)

    if len(sys.argv) <= 1:
	print usage
	sys.exit(1)

    # Configurable settings
    global debug
    debug = 0
    global verbose
    verbose = 0
    configfile = None
    global logfile
    logfile = None
    elvin_url = ELVIN_URL
    elvin_scope = ELVIN_SCOPE

    # Handle command-line arguments
    options = "dhvc:e:s:l:"
    long_options = ["debug", "help", "verbose", "configfile=", "elvin_url=", "elvin_scope=", "logfile="]
    try:
	opts, args = getopt.getopt(sys.argv[1:], options, long_options)
    except getopt.GetoptError:
	print usage
	sys.exit(1)
    for o, a in opts:
	if o in ("-h", "--help"):
	    print usage
	    sys.exit(1)
	if o in ("-v", "--verbose"):
	    verbose = 1
	if o in ("-d", "--debug"):
	    debug = 1
	    verbose = 1
	if o in ("-c", "--configfile"):
	    configfile = a
	if o in ("-e", "--elvinurl"):
	    elvin_url = a
	if o in ("-s", "--elvinscope"):
	    elvin_scope = a
	if o in ("-l", "--logfile"):
	    logfile = a

    if verbose:
	log( "elvinrrd version %s starting" % (__version__) )

    # Build config
    if configfile == None:
	sys.stderr.write( "error: No configfile defined\n" )
	sys.exit(1)

    rrddict = ReadConfig( configfile )
    if rrddict == None or rrddict == {}:
	sys.stderr.write( "error: configuration is empty\n" )
	sys.exit(1)

    # Create RRDtool object
    #rrd = RRDtool.RRDtool()
    # Create pointer to rrdtool module
    rrd = rrdtool

    e = storeconsumer(elvin_url, elvin_scope)
    e.rrd = rrd
    e.rrddict = rrddict
    e.register()
    if verbose:
	log( "Starting Elvin main loop" )
    e.elvinc.run()


if __name__ == "__main__":
    try:
	main()
    except:
	e = sys.exc_info()
	tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	errstr = "Uncaught exception:\ %s, %s\n%s" % (e[0], e[1], tb)
	sys.stderr.write( "elvinrrd.py: "+errstr )
	if logfile:
	    log( errstr )
	sys.exit(1)

###
### End of estored.py
###
