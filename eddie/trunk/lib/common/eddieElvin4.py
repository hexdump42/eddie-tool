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

import time, sys, traceback
import log

UseElvin = 1	# Switch Elvin usage on by default

try:
    import elvin
except ImportError:
    # no Elvin modules... disable Elvin
    UseElvin = 0
    log.log( "<eddieElvin4>ImportError: Elvin4 not available - disabling Elvin functions", 3 );


################################################################
## Exceptions:
ElvinError = 'ElvinError'


class elvinConnection:
    """A shared object which maintains a single connection to the Elvin server."""

    def __init__(self, url=ELVINURL, scope=ELVINSCOPE):
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
	    self.elvinc = elvin.connect(constr)

	except:
	    log.log("<eddieElvin4>Connection to elvin failed. Tried to connect with '%s'. Error: %s, %s" %(constr, sys.exc_type, sys.exc_value), 2)
	    sys.stderr.write("Connection to elvin failed. Tried to connect with '%s'\n Error: %s, %s\n" %(constr, sys.exc_type, sys.exc_value))
	    raise ElvinError, "Connection failed to %s" % (constr)
	else:
	    self.connected = 1


    def _exit(self):
	elvinc.close()


    def _destroy(self):
	self._exit()


#    def notify( *args ):
#	print "args:",args
#	self.elvinc.notify( args )


class eddieElvin:

    def __init__(self):
	if UseElvin:
	    global ec			# single global Elvin4 connection object
	    try:
		if ec == None:		# if not set, try to connect
		    ec = elvinConnection()

	    except NameError:		# if ec undefined, we haven't connected yet
		ec = elvinConnection()

	    self.connected = 1
	    log.log( "<eddieElvin>eddieElvin.__init__(), Connected to Elvin server", 6 )

	else:
	    log.log( "<eddieElvin>eddieElvin.__init__(), not connecting because UseElvin=0", 3 )


    # must override this method
    def sendmsg(self,msg):
	if self.connected:
	    try:
		ec.elvinc.notify( TICKERTAPE = 'Eddie',
	                          TICKERTEXT = msg,
				        USER = log.hostname,
			             TIMEOUT = 10, 
			           MIME_TYPE = 'x-elvin/slogin',
			           MIME_ARGS = log.hostname )
	    except:
		e = sys.exc_info()
                tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		log.log( "<eddieElvin>eddieElvin.sendmsg(), notify failed: %s, %s, %s." % (e[0], e[1], tb), 3 )
		return 1

	    return 0

	else:
	    return 1




class elvinTicker(eddieElvin):
    """Send a standard Elvin tickertape message to the Tickertape group 'Eddie'.
       The Tickertape user will be the hostname of the machine sending the message.
    """

    def __init__(self):
        apply( eddieElvin.__init__, (self,) )

    def sendmsg(self,msg):
	if self.connected:
	    try:
		ec.elvinc.notify( TICKERTAPE = 'Eddie',
			          TICKERTEXT = msg,
				        USER = log.hostname,
			             TIMEOUT = 10, 
			           MIME_TYPE = 'x-elvin/slogin',
			           MIME_ARGS = log.hostname )
	    except:
		e = sys.exc_info()
                tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		log.log( "<eddieElvin>elvinTicker.sendmsg(), notify failed: %s, %s, %s." % (e[0], e[1], tb), 3 )
		return 1

	    log.log( "<eddieElvin>elvinTicker.sendmsg(), notify successful: '%s'" % (msg), 9 )
	    return 0

	else:
	    return 1



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

	if self.connected:
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

		ec.elvinc.notify( edict )

	    return 0

	else:
	    return 1


class elvinrrd(eddieElvin):
    """Send a dictionary through Elvin to a listener process which should store
       the data into an RRDtool database.  Supports Elvin4+ only."""

    def __init__(self):
        apply( eddieElvin.__init__, (self,) )


    def send(self, key, variable, data):
	"""Send the message.
	"""

	#timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

	if self.connected:
	    # Create db entry creation 'command'
	    edict = {      'ELVINRRD' : key,
		             variable : data
		    }

	    ec.elvinc.notify( edict )

	    return 0

	else:
	    return 1


##
## END - eddieElvin4.py
##
