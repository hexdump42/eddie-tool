## 
## File         : eddieElvin4.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Date         : 20010527
## 
## Description  : Elvin4 messaging interface
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001
##
## The author accepts no responsibility for the use of this software and
## provides it on an ``as is'' basis without express or implied warranty.
##
## Redistribution and use in source and binary forms are permitted
## provided that this notice is preserved and due credit is given
## to the original author and the contributors.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
########################################################################

################################################################

## Default Elvin server settings.  These are overridden by ELVINURL
##  and ELVINSCOPE config file options.
ELVINURL='elvin://elvin'
ELVINSCOPE='elvin'


## Imports: Python
import time, sys, traceback, threading
## Imports: Eddie
import log


UseElvin = 1	# Switch Elvin usage on by default

try:
    import elvin
    global ec			# single global Elvin4 connection object
    ec = None
except ImportError:
    # no Elvin modules... disable Elvin
    UseElvin = 0
    log.log( "<eddieElvin4>ImportError: Elvin4 not available - disabling Elvin functions", 3 );


################################################################
## Exceptions:
ElvinError = 'ElvinError'


class elvinConnection:
    """A shared object which maintains a single connection to the Elvin server."""

    def __init__(self, url, scope):
	self.url = url
	self.scope = scope

	if UseElvin == 0:
	    raise ElvinError, "Elvin not available"

	if self.url != "":
	    constr = self.url		# use specific URL
	elif self.scope != "":
	    constr = self.scope		# use Elvin Scope
	else:
	    constr = ""			# use server discovery

	try:
	    log.log("<eddieElvin4>Attempting to connect to Elvin, '%s'" %(constr), 7)
	    self.elvinc = elvin.connect(constr)

	except:
	    log.log("<eddieElvin4>Connection to elvin failed. Tried to connect with '%s'. Error: %s, %s" %(constr, sys.exc_type, sys.exc_value), 2)
	    raise ElvinError, "Connection failed to %s" % (constr)


    def _exit(self):
	elvinc.close()


    def _destroy(self):
	self._exit()


elvin_connect_semaphore = threading.Semaphore()

class eddieElvin:

    def __init__(self):
	if UseElvin:
	    self.connect()		# make an Elvin connection
	else:
	    log.log( "<eddieElvin4>eddieElvin.__init__(), Elvin functionality disabled - probably because modules do not exist", 3 )


    def connect(self):
	"""Try to make an Elvin connection."""

	log.log( "<eddieElvin4>eddieElvin.connect(), acquiring semaphore lock...", 8 )
	elvin_connect_semaphore.acquire()	# semaphore lock around Elvin connect
						# only 1 thread connects at a time
	log.log( "<eddieElvin4>eddieElvin.connect(), got semaphore lock", 8 )

	global ec

	maxtries = 3			# max number of attempts to connect

	tries = 0
	tryagain = 1
	while tryagain:
	    tryagain = 0
	    tries = tries + 1
	    if tries > maxtries:
		break

	    try:
		if ec == None:		# if not set, try to connect
		    ec = elvinConnection( url=ELVINURL, scope=ELVINSCOPE )
		    log.log( "<eddieElvin4>eddieElvin.connect(), Connected to Elvin server, url='%s' scope='%s'" % (ELVINURL, ELVINSCOPE), 6 )
	    except elvin.errors.ElvinConnectNotReady:
		log.log( "<eddieElvin4>eddieElvin.connect(), received ElvinConnectNotReady - trying again", 8 )
		tryagain = 1
		time.sleep(5)
	    except:
		e = sys.exc_info()
		tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		log.log( "<eddieElvin4>eddieElvin.connect(), connect failed: %s, %s, %s." % (e[0], e[1], tb), 3 )
		elvin_connect_semaphore.release()	# release lock
		return 1

	if not ec:
	    log.log( "<eddieElvin4>eddieElvin.connect(), Could not connect to Elvin server", 4 )

	log.log( "<eddieElvin4>eddieElvin.connect(), releasing semaphore lock", 8 )
	elvin_connect_semaphore.release()	# release lock


    def reconnect(self):
	global ec

	log.log( "<eddieElvin4>eddieElvin.reconnect(), attempting to reconnect to server", 7 )
	try:
	    ec.elvinc.close()	# try to close connection, just in case
	except:
	    pass

	ec = None
	self.connect()


    def notify(self, msg):
        """Send an Elvin notification.  msg must be a dictionary."""

	global ec

	if UseElvin == 0:
	    log.log( "<eddieElvin4>eddieElvin.notify(), Elvin is disabled - request ignored", 7 )
	    return 2

	if not ec:
	    # if not connected to Elvin, try to connect again
	    log.log( "<eddieElvin4>eddieElvin.notify(), not connected - calling connect()", 7 )
	    self.connect()

	if ec:
	    maxtries = 3			# max number of attempts to try

	    tries = 0
	    tryagain = 1
	    while tryagain:
		tryagain = 0
		tries = tries + 1
		if tries > maxtries:
		    break

		try:
		    ec.elvinc.notify( nfn=msg )
		except elvin.errors.ElvinConnectNotReady:
		    log.log( "<eddieElvin4>eddieElvin.notify(), received ElvinConnectNotReady - trying again", 8 )
		    tryagain = 1
		    time.sleep(5)
		except:
		    e = sys.exc_info()
		    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		    log.log( "<eddieElvin4>eddieElvin.notify(), notify failed: %s, %s, %s." % (e[0], e[1], tb), 3 )
		    return 1

	    if tries > maxtries:
		log.log( "<eddieElvin4>eddieElvin.notify(), too many retries - trying to reconnect", 4 )
		self.reconnect()
		return 1

	else:
	    log.log( "<eddieElvin4>eddieElvin.notify(), no connection - cannot send Elvin message", 7 )
	    self.reconnect()
	    return 1

	return 0


    def send(self, text='test'):
	"""A template send() function.  Override this method to customise it."""

	msg = { 'TICKERTAPE': 'Eddie',
		'TICKERTEXT': text,
		      'USER': log.hostname,
		   'TIMEOUT': 10
	      }

	r = self.notify( msg )	# Send Elvin message

	if r != 0:
	    print "Elvin send failed..."



class elvinTicker(eddieElvin):
    """Send a standard Elvin tickertape message to the Tickertape group 'Eddie'.
       The Tickertape user will be the hostname of the machine sending the message.
    """

    def __init__(self):
        apply( eddieElvin.__init__, (self,) )


    def sendmsg(self, msg):
	"""Send an Elvin Tickertape message.  msg is the text string to send."""

	elvinmsg = { 'TICKERTAPE': 'Eddie',
		     'TICKERTEXT': msg,
			   'USER': log.hostname,
			'TIMEOUT': 10, 
		      'MIME_TYPE': 'x-elvin/slogin',
		      'MIME_ARGS': log.hostname
		   }

	r = self.notify( elvinmsg )	# Send Elvin message

	if r != 0:
	    log.log( "<eddieElvin4>elvinTicker.sendmsg(), notify failed, msg '%s'" % (msg), 4 )
	    return r	# failed

	else:
	    log.log( "<eddieElvin4>elvinTicker.sendmsg(), notify successful, msg '%s'" % (msg), 8 )
	    return r	# succeeded


class elvindb(eddieElvin):
    """Send a dictionary through Elvin to a listener process which should store
       the data into a database.  Supports Elvin4+ only."""

    def __init__(self):
        apply( eddieElvin.__init__, (self,) )


    def send(self, table, data):
	"""Send the dictionary, aimed for table 'table' in db.
	   - 'table' is a string specifying which table to insert the data into.
	   - 'data' is a dictionary of data.
	"""

	# If any of the data in 'data' is a dictionary, save these off
	# separately and send each one over Elvin.
	extrahashes = {}

	for i in data.keys():
	    if type(data[i]) == type({}):
		extrahashes[i] = data[i]
		del data[i]

	timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

	# Create db entry creation 'command'
	edict = {      'ELVIN.TABLE' : table,
		     'ELVIN.COMMAND' : 'CREATE',
			'ELVIN.HOST' : log.hostname,
			   'ELVINDB' : 'ELVINDB',	# For consumers to subscribe for
		   'ELVIN.TIMESTAMP' : timestamp
		}

	if len(extrahashes) > 0:
	    for e in extrahashes.keys():
		edictcopy = {}
		edictcopy.update(edict)
		edictcopy.update(extrahashes[e])		# add all the system data

	else:
	    edict.update(data)		# add all the system data

	r = self.notify( edict )	# Send Elvin message

	if r != 0:
	    log.log( "<eddieElvin4>elvinTicker.elvindb(), notify failed, table %s" % (table), 4 )
	    return r	# failed

	else:
	    log.log( "<eddieElvin4>elvinTicker.elvindb(), notify successful table %s" % (table), 8 )
	    return r	# succeeded


class elvinrrd(eddieElvin):
    """Send a dictionary through Elvin to a listener process which should store
       the data into an RRDtool database.  Supports Elvin4+ only."""

    def __init__(self):
        apply( eddieElvin.__init__, (self,) )


    def send(self, key, data):
	"""Send the message.
	"""

	# Create db entry creation 'command'
	edict = {      'ELVINRRD' : key
		}
	edict.update(data)		# add data dictionary to edict

	r = self.notify( edict )	# Send Elvin message

	if r != 0:
	    log.log( "<eddieElvin4>elvinTicker.elvinrrd(), notify failed, key %s" % (key), 4 )
	    return r	# failed

	else:
	    log.log( "<eddieElvin4>elvinTicker.elvinrrd(), notify successful, key %s" % (key), 8 )
	    return r	# succeeded

##
## END - eddieElvin4.py
##
