## 
## File		: pop3.py 
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 20000616
## 
## Description	: Directives for pop3 checks
##
## $Id$
##
##


# Imports: Python
import sys, os, commands, socket, time
# Imports: Eddie
import log, directive, utils


# Define exceptions
POP3error = "POP3error"


class pop3:
    """A simple pop3 client."""

    def __init__(self, host, port=110):
	if host == "":
	    raise POP3error, "host not given"

	if type(port) != type(1):
	    raise POP3error, "port must be integer"

	self.host = host
	self.port = port
	self.username = None
	self.password = None
	self.connected = 0
	self.authenticated = 0


    def connect(self):
	self.pop3sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	tstart = time.time()
	try:
	    self.pop3sock.connect(self.host, self.port)
	except socket.error, detail:
	    log.log( "<solaris.py>pop3.connect(): exception, %d, '%s'" % (detail[0], detail[1]), 3 )
	    return 0

	data = self.pop3sock.recv(1024)
	tend = time.time()

	if data[:3] != "+OK":
	    return 0

	self.connected = 1
	self.timing = tend - tstart
	return 1


    def close(self):
	if self.connected == 0:
	    raise POP3error, "no connection to close"

	self.pop3sock.close()
	self.connected = 0
	self.authenticated = 0


    def auth(self, username, password=""):
	if self.connected == 0:
	    raise POP3error, "no connection"
	if self.authenticated == 1:
	    raise POP3error, "already authenticated"

	tstart = time.time()
	self.pop3sock.send( "user %s\n"%(username) )
	data = self.pop3sock.recv(1024)
	if data[:3] == "+OK":
	    self.pop3sock.send( "pass %s\n"%(password) )
	    data = self.pop3sock.recv(1024)
	    if data[:3] == "+OK":
		self.authenticated = 1
	tend = time.time()

	self.timing = tend - tstart

	self.username = username
	# don't store password........

	if self.authenticated == 0:
	    return 0			# failed
	else:
	    return 1			# success


    def list(self):
	"""Send a POP3 LIST command.
	Returns the number of messages reported by server.
	Returns 0 if failed.
	Does not do anything with the list of messages.
	"""

	if self.connected == 0:
	    raise POP3error, "no connection"
	if self.authenticated == 0:
	    raise POP3error, "not authenticated"

	tstart = time.time()
	self.pop3sock.send( "list\n" )
	data = self.pop3sock.recv(24000)
	tend = time.time()
	if data[:3] == "+OK":
	    listok = 1
	    try:
		import re
		nummsgs = int(re.search( "\+OK ([0-9]+) messages.*", data ).group(1))
	    except:
		nummsgs = 0
	else:
	    listok = 0

	# TODO: get actual listing and store nicely...

	self.timing = tend - tstart

	if listok == 0:
	    return 0			# failed
	else:
	    return nummsgs		# success


    def retr(self, msg):
	"""Send a POP3 RETR command.
	"""

	if self.connected == 0:
	    raise POP3error, "no connection"
	if self.authenticated == 0:
	    raise POP3error, "not authenticated"

	tstart = time.time()
	self.pop3sock.send( "retr %d\n"%(msg) )
	data = self.pop3sock.recv(64000)
	tend = time.time()
	if data[:3] == "+OK":
	    retrok = 1
	    try:
		import re
		msgsize = int(re.search( "\+OK ([0-9]+) octets.*", data ).group(1))
	    except:
		msgsize = 0
	else:
	    retrok = 0

	# TODO: do something with message perhaps?

	self.timing = tend - tstart

	if retrok == 0:
	    return 0			# failed
	else:
	    return msgsize		# success



## Directives ##


class POP3TIMING(directive.Directive):
    """POP3TIMING directive.  Make a pop3 connection and time various
       actions such as connecting, authenticating, retrieving messages,
       etc.

       Sample rule:
       POP3TIMING: 'hostname:port' 'username' 'password' <actions>
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):

	self.hostport = utils.stripquote(toklist[0])	# hostname:port
	self.username = utils.stripquote(toklist[1])	# username
	self.password = utils.stripquote(toklist[2])	# password
	self.actionList = self.parseAction(toklist[3:])

	if ':' in self.hostport:
	    (self.host, self.port) = string.split( self.hostport, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.hostport
	    self.port = 110


	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['pop3timinghost'] = self.host
	self.Action.varDict['pop3timingport'] = self.port
	self.Action.varDict['pop3timingusername'] = self.username
	self.Action.varDict['pop3timingpassword'] = self.password

	# define the unique ID
	self.ID = '%s.POP3TIMING.%s.%d.%s' % (log.hostname,self.host,self.port,self.username)

	log.log( "<pop3.py>POP3TIMING.tokenparser(): ID '%s' host '%s' port %d username '%s'" % (self.ID, self.host, self.port, self.username), 8 )


    def docheck(self, Config):
	"""The 'check' in this case is to login to the pop3 server and
	perform a few actions, recording the timing of each action.
	The directive actions are always called.  Usually these will
	record the timing details in some way."""

	log.log( "<pop3.py>POP3TIMING.docheck(): host '%s' port %d username '%s'" % (self.host, self.port, self.username), 7 )

	connecttime = None
	authtime = None
	listtime = None
	retrtime = None

	# create pop3 connection object
	p = pop3( self.host, self.port )
	if p.connect():			# login to pop3 server
	    connecttime = p.timing	# get timing for connection to return banner

	    if p.auth( self.username, self.password ):	# authenticate user
		authtime = p.timing	# get timing for authentication

		l = p.list()		# list email headers
		listtime = p.timing	# timing for list

		if l > 0:
		    p.retr(1)		# retrieve first email
		    retrtime = p.timing	# get retr timing

	    p.close()



	self.state.stateok()	# update state info for check passed

	# assign variables
	self.Action.varDict['pop3timingconnecttime'] = connecttime
	self.Action.varDict['pop3timingauthtime'] = authtime
	self.Action.varDict['pop3timinglisttime'] = listtime
	self.Action.varDict['pop3timingretrtime'] = retrtime

	# Values are set to None if there was some problem performing the
	# commands.
	if connecttime == None:
	    connecttime = 0
	    log.log( "<pop3.py>POP3TIMING.docheck(): connecttime could not be measured, setting to 0", 3 )
	if authtime == None:
	    authtime = 0
	    log.log( "<pop3.py>POP3TIMING.docheck(): authtime could not be measured, setting to 0", 3 )
	if listtime == None:
	    listtime = 0
	    log.log( "<pop3.py>POP3TIMING.docheck(): listtime could not be measured, setting to 0", 3 )
	if retrtime == None:
	    retrtime = 0
	    log.log( "<pop3.py>POP3TIMING.docheck(): retrtime could not be measured, setting to 0", 3 )

	log.log( "<pop3.py>POP3TIMING.docheck(): connecttime=%s authtime=%s listtime=%s retrtime=%s" % (connecttime, authtime, listtime, retrtime), 8 )

	self.doAction(Config)



##
## END - pop3.py
##
