
'''
File            : eddieElvin4.py 

Start Date      : 20010527

Description     : Elvin4 messaging interface

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

__author__ = 'Chris Miles'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''


## Imports: Python
import time
import sys
import traceback
import threading
import Queue
## Imports: Eddie
import log


## Default Elvin server settings - empty means Elvin is disabled.
## These are overridden by ELVINURL and ELVINSCOPE config file options.
ELVINURL=''
ELVINSCOPE=''


## Constants
ANYTIME=-1
BLOCK=1


## Globals
UseElvin = 1	# Switch Elvin usage on by default; disabled if modules not found


## Import elvin python modules if possible
try:
    import elvin
except ImportError:
    # no Elvin modules... disable Elvin
    UseElvin = 0


################################################################
## Exceptions:
ElvinError = 'ElvinError'
ElvinInitError = 'ElvinInitError'


################################################################
## Message class
class Message:
    """Defines an Elvin message object which will be placed in the
    message queue waiting to be sent. Normally it will be sent instantly
    but it is possible (like when Elvin server is down or network is
    unavailable) that the message could be sent some time after being
    inserted into the queue.
    Besides the notification message itself, this object contains a
    time parameter defining how long after being inserted into the
    queue the message is still valid for sending."""

    def __init__(self, emsg, validity_time):
	self.emsg = emsg			# the notification message
	self.validity_time = validity_time	# message validity time (minutes)
	self.timestamp = time.time()		# store object creation time


    def __str__(self):
	string = str(self.emsg)
	return(string)


    def time_valid(self):
	"""Calculate if message is still valid to be sent based on when
	it was created (self.timestamp) and the validity time
	(self.validity_time) setting."""

	if self.validity_time == ANYTIME:
	    return 1		# don't care when message is sent

	now = time.time()
	if (now-self.timestamp) <= self.validity_time*60.0:
	    return 1		# message still valid
	else:
	    return 0		# no longer valid to send



################################################################
## Elvin class
class Elvin:
    """Sets up Elvin connections if possible and starts dedicated Elvin
    thread to handle all messaging."""

    def __init__(self):

	global UseElvin
	if UseElvin == 0:
	    raise ElvinInitError, "Elvin modules not found"

	if not ELVINURL and not ELVINSCOPE:
	    UseElvin = 0
	    raise ElvinInitError, "Elvin administratively disabled"

	self.eq = Queue.Queue()		# Elvin message queue

	##-- create Elvin client using ThreadedLoop
	#log.log( "<eddieElvin4>Elvin.__init__(): Creating elvin client (ThreadedLoop)", 8 )
	#self.client = elvin.client(elvin.ThreadedLoop)
	#-- create Elvin client using SyncLoop
	log.log( "<eddieElvin4>Elvin.__init__(): Creating elvin client (SyncLoop)", 5 )
	self.client = elvin.client(elvin.SyncLoop)


    def startup(self):
	"""Start the Elvin management thread."""

	self.ethread = threading.Thread(group=None, target=self.main, name='Elvin', args=(), kwargs={})
	self.ethread.setDaemon(1)	# die automatically when Main thread dies
	self.ethread.start()		# start the thread running


    def main(self):
	"""The Elvin management thread."""

	waittime = 1				# time to wait before re-connecting

	while 1:
	    status = self.connect()		# open Elvin connection
	    if status:
		self.subscribe()		# setup any subscriptions
		waittime = 1			# reset wait time

		# Loop to watch message queue for any Elvin notifications to be sent
		#   from other Elvin functions or actions.
		# This means no other threads should block when sending Elvin notifications.
		while self.connection.is_open():
		    m = self.eq.get(BLOCK)	# get next message or wait for one
		    if m.time_valid():
			log.log("<eddieElvin4>Elvin.main(): Sending msg from queue, %s"%(m), 9)
			try:
			    self.connection.notify(m.emsg)
			    log.log("<eddieElvin4>Elvin.main(): msg sent, %s"%(m), 6)
			except elvin.ElvinConnectNotReady, details:
			    log.log("<eddieElvin4>Elvin.main(): Elvin exception, %s, msg %s not sent"%(details, m), 3)
			    self.eq.put(m)	# put msg back in queue for re-try
		    else:
			log.log("<eddieElvin4>Elvin.main(): message no longer valid, discarding %s"%(m), 9)

	    else:
		log.log("<eddieElvin4>Elvin.main(): Elvin connect failed waiting %d secs"%(waittime), 5)
		time.sleep( waittime )
		waittime = min( waittime * 2, 60*60*4 ) # inc wait time but max 4 hours

	    log.log("<eddieElvin4>Elvin.main(): Elvin connection closed...  reconnecting", 4)


    def connect(self):
	"""Create an Elvin connection, using either a specified Elvin Scope
	or an Elvin URL."""

	self.url = ELVINURL		# as set by eddie.cf config
	self.scope = ELVINSCOPE

	# Create Elvin connection
	self.connection = self.client.connection()
	self.connection.set_discovery(0)	# disable auto-discovery

	# Create the connect string; if a URL is specified then use that
	# otherwise use the Scope if available, otherwise use server
	# discovery (see Elvin documentation for details).
	if self.url != "":
	    self.connection.insert_url(0, self.url)
	    self.connect_str = self.url
	elif self.scope != "":
	    self.connection.set_scope(self.scope)
	    self.connect_str = self.scope
	else:
	    self.connect_str = '*'

	# Now open connection to server
	log.log("<eddieElvin4>Elvin.connect(): Opening connection to Elvin, '%s'" %(self.connect_str), 5)
	status = 0

	try:
	    self.connection.open()
	except elvin.ElvinConnectMaxRetries, msg:
	    log.log("<eddieElvin4>Elvin.connect(): Elvin could not connect, ElvinConnectMaxRetries '%s'" %(msg), 5)
	else:
	    log.log("<eddieElvin4>Elvin.connect(): Connected to Elvin, '%s'" %(self.connect_str), 5)
	    status = 1

	return status


    def notify(self, emsg, validity_time=ANYTIME):
	"""Add Elvin notification message to message queue to be sent by
	main Elvin management thread as soon as possible."""

	m = Message(emsg, validity_time)
	self.eq.put(m)

	return 0


    def subscribe(self):
	# Not in use, yet
	pass
        #-- add subscription
	#substr = 'require(TEST)'
        #sub = self.connection.subscribe(substr, 1, None)
        #sub.add_listener(self._sub_cb, self.connection)
        #sub.register()


    def _sub_cb(self, sub, nfn, insec, rock):
	# Not in use, just a sample
        test = nfn['TEST']



    ####################################################
    ## Public methods for Eddie functions/actions to use

    def Ticker(self, msg, timeout):
	"""Send a standard Elvin tickertape message to the Tickertape group 'Eddie'.
	The Tickertape user will be the hostname of the machine sending the message.
	msg is the text string to send (TICKERTEXT).
	"""

	elvinmsg = { 'TICKERTAPE': 'Eddie',
		     'TICKERTEXT': msg,
			   'USER': log.hostname,
			'TIMEOUT': timeout
#		      'MIME_TYPE': 'x-elvin/slogin',
#		      'MIME_ARGS': log.hostname
		   }

	r = self.notify( elvinmsg, validity_time=10 )	# Send Elvin message, within 10 mins

	if r != 0:
	    # failed
	    log.log( "<eddieElvin4>Elvin.Ticker(), notify failed, msg: %s" % (msg), 5 )
	else:
	    # succeeded
	    log.log( "<eddieElvin4>Elvin.Ticker(), msg added to queue, msg: %s" % (msg), 6 )

	return r


    def elvindb(self, table, data):
	"""Send a dictionary through Elvin to a listener process which should store
        the data into a database.
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
	    # failed
	    log.log( "<eddieElvin4>Elvin.elvindb(): notify failed, table:%s" % (table), 5 )
	else:
	    log.log( "<eddieElvin4>Elvin.elvindb(): message added to queue, table:%s" % (table), 6 )

	return r


    def elvinrrd(self, key, data):
	"""Send a dictionary through Elvin to a listener process which should store
        the data into an RRDtool database.
	 - 'key' will be matched by the elvinrrd consumer
	 - 'data' is a dictionary of data to be sent in the message
	"""

	# Create db entry creation 'command'
    edict = {
        'ELVINRRD' : key,
        'timestamp' : time.time(),
    }
	edict.update(data)		# add data dictionary to edict

	r = self.notify( edict )	# Send Elvin message

	if r != 0:
	    # failed
	    log.log( "<eddieElvin4>Elvin.elvinrrd(): notify failed, key:%s" % (key), 5 )
	else:
	    log.log( "<eddieElvin4>Elvin.elvinrrd(): msg added to notify queue, key:%s" % (key), 6 )

	return r


    def netsaint(self,data):
	"""
	by Dougal Scott <dwagon@connect.com.au>
	"""

        edict = { 'NETSAINT' : 'NETSAINT' }
        edict.update(data)              # add data dictionary to edict
        r = self.notify( edict )        # Send Elvin message
        if r != 0:
            log.log( "<eddieElvin4>Elvin.netsaint(): notify failed", 4 )
            return r            # failed
        else:
            log.log( "<eddieElvin4>Elvin.netsaint(): notify successful", 8 )
            return r            # succeeded


##
## END - eddieElvin4.py
##
