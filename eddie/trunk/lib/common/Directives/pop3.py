## 
## File		: pop3.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20000616
## 
## Description	: Directives for pop3 checks
##
## $Id$
##
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


# Imports: Python
import socket, time
# Imports: Eddie
import log, directive


# Define exceptions
POP3error = "POP3error"


class pop3:
    """
    A simple pop3 client.
    Used by the Eddie Directives in this module.
    """

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
	    self.pop3sock.connect( (self.host,self.port) )
	except socket.error, detail:
	    log.log( "<pop3>pop3.connect(): exception, %d, '%s'" % (detail[0], detail[1]), 5 )
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
	"""
	Send a POP3 RETR command.
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



##
## Directives
##

class POP3TIMING(directive.Directive):
    """
    POP3TIMING directive.  Make a pop3 connection and time various
    actions such as connecting, authenticating, retrieving messages,
    etc.

    Directive format:
       POP3TIMING test: server='hostname[:port]'
                        user='username'
			password='password'
			rule=1			# always call action
			action="<actions>"
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""
	Parse directive arguments.
	"""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.server		# hostname:port
        except AttributeError:
            raise directive.ParseFailure, "POP3 Server not specified"
	try:
	    self.args.user		# username
        except AttributeError:
            raise directive.ParseFailure, "Username not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	try:
	    self.args.password	# password
        except AttributeError:
            raise directive.ParseFailure, "Password not specified"

	if ':' in self.args.server:
	    (self.host, self.port) = string.split( self.server, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.args.server
	    self.port = 110


	# Set variables for Actions to use
	self.defaultVarDict['server'] = self.host
	self.defaultVarDict['port'] = self.port
	self.defaultVarDict['username'] = self.args.user
	self.defaultVarDict['password'] = self.args.password

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.POP3TIMING.%s.%d.%s' % (log.hostname,self.host,self.port,self.args.user)
	self.state.ID = self.ID

	log.log( "<pop3>POP3TIMING.tokenparser(): ID '%s' host '%s' port %d user '%s'" % (self.ID, self.host, self.port, self.args.user), 8 )


    def getData(self):
	"""
	The 'check' in this case is to login to the pop3 server and
	perform a few actions, recording the timing of each action.
	"""

	data = {}

	connecttime = None
	authtime = None
	listtime = None
	retrtime = None

	# create pop3 connection object
	p = pop3( self.host, self.port )
	if p.connect():			# login to pop3 server
	    data['connected'] = 1
	    connecttime = p.timing	# get timing for connection to return banner

	    if p.auth( self.args.user, self.args.password ):	# authenticate user
		authtime = p.timing	# get timing for authentication

		l = p.list()		# list email headers
		listtime = p.timing	# timing for list

		if l > 0:
		    p.retr(1)		# retrieve first email
		    retrtime = p.timing	# get retr timing

	    p.close()

	else:
	    data['connected'] = 0

	# assign variables
	data['connecttime'] = connecttime
	data['authtime'] = authtime
	data['listtime'] = listtime
	data['retrtime'] = retrtime

	log.log( "<pop3>POP3TIMING.getData(): connecttime=%s authtime=%s listtime=%s retrtime=%s" % (connecttime, authtime, listtime, retrtime), 7 )

        return data



##
## END - pop3.py
##
