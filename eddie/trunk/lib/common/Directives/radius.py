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
	    self.args.server		# hostname:port
	except AttributeError:
	    raise directive.ParseFailure, "Server not specified"
	try:
	    self.args.secret		# secret
	except AttributeError:
	    raise directive.ParseFailure, "Secret not specified"
	try:
	    self.args.user		# username
	except AttributeError:
	    raise directive.ParseFailure, "Username not specified"
	try:
	    self.args.password	# password
	except AttributeError:
	    raise directive.ParseFailure, "Password not specified"

	if ':' in self.args.server:
	    (self.host, self.port) = string.split( self.args.server, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.args.server
	    self.port = 1645


	# Set any directive-specific variables
	self.Action.varDict['radiushost'] = self.host
	self.Action.varDict['radiusport'] = self.port
	self.Action.varDict['radiussecret'] = self.args.secret
	self.Action.varDict['radiususername'] = self.args.user
	self.Action.varDict['radiuspassword'] = self.args.password

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.RADIUS.%s.%d.%s' % (log.hostname,self.host,self.port,self.args.user)
	self.state.ID = self.ID

	log.log( "<radius>RADIUS.tokenparser(): ID '%s' host '%s' port %d secret '%s' user '%s'" % (self.ID, self.host, self.port, self.args.secret, self.args.user), 8 )


    def docheck(self, Config):
	"""Perform a Radius authentication and return results."""

	log.log( "<radius>RADIUS.docheck(): host '%s' port %d user '%s'" % (self.host, self.port, self.args.user), 7 )

	timing = None

	# create pop3 connection object
	r = radcm.Radius( self.host, self.args.secret, self.port  )
	tstart = time.time()
	try:
	    z = r.authenticate(self.args.user,self.args.password)
	except radcm.NoResponse:
	    z = None
	tend = time.time()
	timing = tend - tstart

	# Values are set to None if there was some problem performing the
	# commands.
	if timing == None:
	    timing = 0
	    log.log( "<radius>RADIUS.docheck(): timing could not be measured, setting to 0", 3 )

	# assign variables
	self.Action.varDict['radiustiming'] = timing

	log.log( "<radius>RADIUS.docheck(): timing=%s z=%s" % (timing,z), 8 )


	self.state.statefail()	# set to fail before calling doAction()
	self.doAction(Config)

	if z:
	    self.state.stateok()	# update state info for check passed

        self.putInQueue( Config.q )     # put self back in the Queue



##
## END - radius.py
##
