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

__version__ = """$Revision$"""[11:-2]

################################################################

import sys, traceback, re, string
import RRDtool	# requires PyRRDtool from http://cvsweb.extreme-ware.com/cvsweb.cgi/PyRRDtool/
import elvin	# requires Elvin4 modules from http://elvin.dstc.edu.au/

ELVIN_URL='elvin://elvin.connect.com.au'
ELVIN_SCOPE='elvin'
RRD_DB = '/var/tmp/test.rrd'

################################################################

class RRDstore:
    """Object with details of what to match in the Elvin message and
       how to store the data in RRD.
    """

    def __init__(self, elvinrrd, rrdfile, store):
	self.elvinrrd = elvinrrd
	self.rrdfile = rrdfile
	self.store = store


    def __str__(self):
	return "[elvinrrd=%s rrdfile=%s store=%s]" % (self.elvinrrd, self.rrdfile, self.store)


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
 
	print "msg:", msg

	try:
	    r = self.rrddict[msg[u'ELVINRRD']]
	    val = msg[u'%s'%(r.store)]
	    u = (r.rrdfile, "N:%s" % (str(val)))
	    print ' rrd.update( %s )' % (u,)
	    self.rrd.update( u )

	except KeyError:
	    print "KeyError with message %s" % (msg)

	except IOError:
	    print "IOError, cannot update rrd file for message %s" % (msg)



def ReadConfig( filename ):
    """Read the configuration from the given filename."""

    rrddict = {}

    try:
        fp = open(filename, 'r')
    except IOError:
        print "Cannot open configuration file '%s', exiting." % (filename)

    re_comment = "^\s*#.*$"
    re_empty = "^\s*$"
    re_line = "^\s*(.+=.+?)\s+(.+=.+?)\s+(.+=.+?)\s*$"

    sre_comment = re.compile(re_comment)
    sre_empty = re.compile(re_empty)
    sre_line = re.compile(re_line)

    line = fp.readline()
    while len(line) > 0:
        if sre_comment.match(line) or sre_empty.match(line):
	    pass	# commented or empty lines are ignored
        else:
            inx = sre_line.match(line)
	    if inx == None:
	        print "Parse error, invalid line follows:\n%s" % (line)
	        sys.exit(1)
            else:
	        for i in range(1,4):
                    (x,y) = string.split( inx.group(i), '=' )
		    if x == 'elvinrrd':
		        elvinrrd = y
		    elif x == 'rrdfile':
		        rrdfile = y
		    elif x == 'store':
		        store = y
		    else:
		        print "Parse error, unknown keyword '%s' on following line:\n%s" % (x,line)
		        sys.exit(1)

	        rrdobj = RRDstore( elvinrrd, rrdfile, store )
	        rrddict[elvinrrd] = rrdobj

        line = fp.readline()

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

#    if not os.path.exists( RRD_DB ):
#	print "Creating new RRD db %s" % (RRD_DB)
#        rrd.create((RRD_DB, "-s 300", "DS:value:GAUGE:600:0:100", "RRA:AVERAGE:0.5:1:1200"))

    e = storeconsumer()
    e.rrd = rrd
    e.rrddict = rrddict
    e.register()
    e.elvinc.run()



###
### End of estored
###
