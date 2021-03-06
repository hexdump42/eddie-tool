#!/opt/local/bin/python
## 
## File         : eddieElvin.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980407
## 
## Description  : Elvin messaging interface
##
## $Id$
##

################################################################

## Default Elvin server hostname and port.  These are overridden by ELVINHOST
##  and ELVINPORT config file options.
ELVINHOST='elvin'
ELVINPORT=5678

import time, types, os, sys, thread, signal, getopt
import log
import snpp

UseElvin = 1	# Switch Elvin usage on by default

try:
    #import Elvin, ElvinMisc
    #from Elvin import *
    import Elvin
except ImportError:
    # no Elvin modules... disable Elvin
    UseElvin = 0
    log.log( "<eddieElvin>ImportError: Elvin not available - disabling Elvin functions", 3 );


################################################################
## Exceptions:
ElvinError = 'ElvinError'


class elvinConnection:
    """A shared object which maintains a single connection to the Elvin server."""

    def __init__(self, host=ELVINHOST, port=ELVINPORT):
	self.host = host
	self.port = port

	if UseElvin == 0:
	    raise ElvinError, "Elvin not available"

	try:
	    self.elvin = Elvin.Elvin(Elvin.EC_NAMEDHOST, self.host, self.port, None, None, self._error_cb)
	except:
	    sys.stderr.write("Connection to elvin failed\nIs there an elvin server running at %s:%d %s/%s\n" %(self.host, self.port, sys.exc_type, sys.exc_value))
	    #self._exit()
	    raise ElvinError, "Connection failed to %s:%d" % (self.host,self.port)
	else:
	    self.connected = 1


    def _error_cb(self, code, msg):
	"""Elvin error callback. We reconnect"""

	sys.stderr.write("Elvin has gone ... will attempt to reconnect\n")
	self.connected = 0
	self._destroy()
	backoff = 10
	while not self._reconnect():
	    time.sleep(backoff)
	    backoff = backoff * 2
#	    if backoff > 36000: # 10 mins
#		sys.stderr.write("Elvin is really dead.  Giving up\n")
#		os.kill(os.getpid(), signal.SIGUSR1)

    def _reconnect(self):
	"""Do the reconnection"""

	try:
	    #sys.stderr.write(" Reconnecting at %s\n"%(time.ctime(time.time()),))
	    log.log( "<eddieElvin>_reconnect(), Reconnecting to Elvin: %s:%d" % (self.host,self.port), 4 )
	    self.elvin = Elvin.Elvin(Elvin.EC_NAMEDHOST, self.host, self.port, None, None, self._error_cb)
	except:
	    sys.exc_traceback = None
	    return 0

	#sys.stderr.write("New Elvin connection established\n")
	log.log( "<eddieElvin>_reconnect(), New Elvin connection established: %s:%d" % (self.host,self.port), 4 )
	self.connected = 1
	return 1


    def _exit(self):
	"""Exit routine. Because the thing that created us is
	sitting on a signal.pause. We signal ourselves to die"""
    
	os.kill(os.getpid(), signal.SIGUSR1)


    def _destroy(self):
	"""Clobber the internal elvin state so we can be deleted"""
	#self.elvin.set_error_cb(None)
	#self.elvin.set_quench_cb(None)
	print "eddieElvin: _destroy() deleting self.elvin"
	del self.elvin



ec=None

class eddieElvin:

    def __init__(self):
	global ec
	#print "eddieElvin init: ec:",ec
	if ec == None:
	    ec = elvinConnection()

	self.connected = ec.connected


    # must override this method
    def sendmsg(self,msg):
	if self.connected:
	    try:
		ec.elvin.notify( { 'TICKERTAPE' : 'Eddie',
	                         'TICKERTEXT' : msg,
				       'USER' : log.hostname,
				    'TIMEOUT' : 10, 
				  'MIME_TYPE' : 'x-elvin/slogin',
				  'MIME_ARGS' : log.hostname } )
	    except Elvin.LostConnectionException:
		log.log( "<eddieElvin>eddieElvin.sendmsg(), notify failed, LostConnectionException.", 3 )
		return 1

	    return 0

	else:
	    return 1




class elvinTicker(eddieElvin):

    def sendmsg(self,msg):
	if self.connected:
	    #self.elvin.notify( { 'TICKERTAPE' : 'Eddie',
	    try:
		self.elvin.notify( { 'TICKERTAPE' : 'EddieTest',
	                         'TICKERTEXT' : msg,
				       'USER' : log.hostname,
				    'TIMEOUT' : 10, 
				  'MIME_TYPE' : 'x-elvin/slogin',
				  'MIME_ARGS' : log.hostname } )
	    except Elvin.LostConnectionException:
		log.log( "<eddieElvin>elvinTicker.sendmsg(), notify failed, LostConnectionException.", 3 )
		return 1

	    return 0

	else:
	    return 1

class elvinPage(eddieElvin):

    def sendmsg(self,pager, msg):
	if self.connected:
	    try:
		self.elvin.notify( { 'ELVINPAGE'  : pager,
	                              'MESS'  : msg    } )
	    except Elvin.LostConnectionException:
		log.log( "<eddieElvin>elvinPage.sendmsg(), notify failed, LostConnectionException.", 3 )
		return 1

	    return 0

	else:
	    return 1

    def subscribe(self):
	
	self.subscription = 'exists(ELVINPAGE)'
        if self.connected:
            self.elvin.subscribe(self.subscription, self._notify_cb)
        else:
            sys.stderr.write("Not connected when at notify time\n")

    def _notify_cb(self, sub_id, d_not):
 
        p = snpp.level1(self.host)
 
        p.pager(d_not['ELVINPAGE'])
        p.message(d_not['MESS'])
 
        try:
            p.send()
        except SNPPpageFail:
            print SNPPpageFail



class elvindb(eddieElvin):
    """Send a dictionary through Elvin to a database listener process."""

    def send(self, table, data):
	"""Send the dictionary, aimed for table 'table' in db.
	- 'table' is a string specifying which table to insert the data into.
	- 'data' is a dictionary of data.
	"""

	# If any of the data in 'data' is a dictionary, save these off
	# separately and send each one over Elvin.
	extrahashes = {}

	# Elvin can't send longs :(
	# Let's get around this for now by converting them to strings!  The
	# consumer at the other end must look for strings containing all digits
	# and ending with a 'L' and convert them back to longs... a hack I know...

	for i in data.keys():
	    if type(data[i]) == type(0L):
		data[i] = "%s" % (data[i])

	    if type(data[i]) == type({}):
		extrahashes[i] = data[i]
		del data[i]

		# and check this sub-dictionary for longs... :(
		for s in extrahashes[i].keys():
		    if type(extrahashes[i][s]) == type(0L):
			extrahashes[i][s] = "%s" % (extrahashes[i][s])

	#print "data:",data
	#print "extrahashes:",extrahashes

	timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

	if self.connected:
	    # Create db entry creation 'command'
	    edict = {      'ELVIN.TABLE' : table,
		         'ELVIN.COMMAND' : 'CREATE',
		            'ELVIN.HOST' : log.hostname,
			       'ELVINDB' : 'ELVINDB',		# put in for the exists() to work - shouldn't be needed...
		       'ELVIN.TIMESTAMP' : timestamp
		    }

	    if len(extrahashes) > 0:
		for e in extrahashes.keys():
		    edictcopy = {}
		    edictcopy.update(edict)
		    edictcopy.update(extrahashes[e])		# add all the system data

		    #self.elvin.notify( edictcopy )
		    try:
			ec.elvin.notify( edictcopy )
		    except Elvin.LostConnectionException:
			log.log( "<eddieElvin>elvindb.send(), notify failed, LostConnectionException.", 3 )
			return 1

	    else:
		edict.update(data)		# add all the system data

		#self.elvin.notify( edict )
		try:
		    ec.elvin.notify( edict )
		except Elvin.LostConnectionException:
		    log.log( "<eddieElvin>elvindb.send(), notify failed, LostConnectionException.", 3 )
		    return 1

	    return 0

	else:
	    return 1



## Test code...

if __name__ == "__main__":

    e = elvinPage()
    e.sendmsg("sysadm", "blah")

    sys.exit(0)



