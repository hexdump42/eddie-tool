#!/opt/python2/bin/python
## 
## File         : elvinrrd.py
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 20010827
## 
## Description  : Elvin4 consumer to insert Eddie STORE data into an RRDtool database.
##
## $Id$
##

################################################################

__version__ = """2.0"""

################################################################

import sys, traceback, re, string, os
import RRDtool	# requires PyRRDtool from http://cvsweb.extreme-ware.com/cvsweb.cgi/PyRRDtool/
import elvin	# requires Elvin4 modules from http://elvin.dstc.edu.au/

ELVIN_URL='elvin://elvin'
ELVIN_SCOPE='elvin'

################################################################

class RRDstore:
    """Object with details of what to match in the Elvin message and
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


    def __str__(self):
	return "[elvinrrd=%s rrdfile=%s store=%s create=%s]" % (self.elvinrrd, self.rrdfile, self.store, self.create)


class eddieElvin:

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	self.elvinurl = elvinurl
	self.elvinscope = elvinscope

	if self.elvinurl and len(self.elvinurl) > 0:
	    connect_string=self.elvinurl
	elif self.elvinscope and len(self.elvinscope) > 0:
	    connect_string=self.elvinscope
	else:
	    connect_string='*'		# auto discovery

	print "Trying Elvin connection to %s" % (connect_string)

	try:
	    self.elvinc = elvin.connect( connect_string )
	    print "Elvin connection succeeded."
	except:
	    sys.stderr.write("Connection to elvin failed - connection string was '%s'\n" % (connect_string) )
	    sys.exit(1)


    def cleanExit(self):
	self.dbcon.close()	# close database connection
	self.elvinc.close()	# close Elvin connection


class storeconsumer(eddieElvin):

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	apply( eddieElvin.__init__, (self, elvinurl, elvinscope) )


    def register(self):

	self.subscription = 'require(ELVINRRD)'

	sub = self.elvinc.subscribe(self.subscription)
	sub.add_listener(self.deliver)
	sub.register()


    def deliver(self, sub, msg, insec, rock):
 
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
	    print "No match for message %s" % (msg)
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

	try:
	    val = msg[u'%s'%(store)]
	except KeyError, err:
	    print "KeyError, %s, message %s" % (err, msg)
	    return 1

	u = (rrdfile, "N:%s" % (str(val)))
	print ' rrd.update( %s )' % (u,)

	try:
	    self.rrd.update( u )
	except IOError, err:
	    if str(err).find('No such file or directory') != -1:
		if os.path.exists( rrdfile ):
		    # file exists, despite the error...
		    print "IOError, %s, message %s" % (err, msg)
		else:
		    print "creating",rrdfile
                    rrd_dir = os.path.dirname( rrdfile )

                    if not os.path.exists( rrd_dir ):
                        print "creating directory", rrd_dir
                        os.makedirs( rrd_dir )

		    createargs = (rrdfile,) + tuple(create.split())
		    print "creating rrd:",createargs
		    rrd.create( createargs )
	    else:
	        print "IOError, %s, message %s" % (err, msg)

	return 0


def ReadConfig( filename ):
    """Read the configuration from the given filename."""

    rrddict = {}

    try:
        fp = open(filename, 'r')
    except IOError:
        print "Cannot open configuration file '%s', exiting." % (filename)

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
		elif inx.group(1) == 'create':
		    create = inx.group(2)
		else:
		    print "Parse error, unknown keyword '%s' on following line:\n%s" % (inx.group(1),line)
		    sys.exit(1)

        line = fp.readline()

    if entry == 1:
	# create new store object
	rrdobj = RRDstore( elvinrrd, rrdfile, store, create )
	rrddict[elvinrrd] = rrdobj

    fp.close()

    return rrddict


if __name__ == "__main__":

    # Build config
    rrddict = ReadConfig( sys.argv[1] )
    if rrddict == None or rrddict == {}:
	print "Error, no configuration."
	sys.exit(1)

    # Create RRDtool object
    rrd = RRDtool.RRDtool()

    e = storeconsumer()
    e.rrd = rrd
    e.rrddict = rrddict
    e.register()
    e.elvinc.run()



###
### End of estored
###
