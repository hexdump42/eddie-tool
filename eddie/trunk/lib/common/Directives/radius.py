## 
## File		: radius.py 
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 20001016
## 
## Description	: Directives for Radius authentication & accounting checks
##
## Requires     : radcm.py
##
## $Id$
##


# Imports: Python
import sys, os, time, string
# Imports: Eddie
import log, directive, utils
# Imports: Misc
import radcm


## Directives ##


class RADIUS(directive.Directive):
    """RADIUS directive.  Perform a Radius authentication and return
       results.

       Sample rule:
       RADIUS: server='hostname[:port]' secret='secret' user='username' password='password' action='<actions>'
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.server		# hostname:port
	except AttributeError:
	    raise ParseFailure, "Server not specified"
	try:
	    self.secret		# secret
	except AttributeError:
	    raise ParseFailure, "Secret not specified"
	try:
	    self.user		# username
	except AttributeError:
	    raise ParseFailure, "Username not specified"
	try:
	    self.password	# password
	except AttributeError:
	    raise ParseFailure, "Password not specified"

	if ':' in self.server:
	    (self.host, self.port) = string.split( self.server, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.server
	    self.port = 1645


	# Set any directive-specific variables
	self.Action.varDict['radiushost'] = self.host
	self.Action.varDict['radiusport'] = self.port
	self.Action.varDict['radiussecret'] = self.secret
	self.Action.varDict['radiususername'] = self.user
	self.Action.varDict['radiuspassword'] = self.password

	# define the unique ID
	self.ID = '%s.RADIUS.%s.%d.%s' % (log.hostname,self.host,self.port,self.user)

	log.log( "<radius>RADIUS.tokenparser(): ID '%s' host '%s' port %d secret '%s' user '%s'" % (self.ID, self.host, self.port, self.secret, self.user), 8 )


    def docheck(self, Config):
	"""Perform a Radius authentication and return results."""

	log.log( "<radius>RADIUS.docheck(): host '%s' port %d user '%s'" % (self.host, self.port, self.user), 7 )

	timing = None

	# create pop3 connection object
	r = radcm.Radius( self.host, self.secret, self.port  )
	tstart = time.time()
	try:
	    z = r.authenticate(self.user,self.password)
	except radcm.NoResponse:
	    z = None
	tend = time.time()
	timing = tend - tstart

	if z:
	    self.state.stateok()	# update state info for check passed
	else:
	    self.state.statefail()	# update state info for check failed

	# Values are set to None if there was some problem performing the
	# commands.
	if timing == None:
	    timing = 0
	    log.log( "<radius>RADIUS.docheck(): timing could not be measured, setting to 0", 3 )

	# assign variables
	self.Action.varDict['radiustiming'] = timing

	log.log( "<radius>RADIUS.docheck(): timing=%s z=%s" % (timing,z), 8 )

	self.doAction(Config)

        Config.q.put( (self,time.time()+self.scanperiod) )      # put self back in the Queue


##
## END - radius.py
##
