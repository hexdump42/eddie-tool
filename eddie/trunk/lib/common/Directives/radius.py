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
       RADIUS: 'hostname[:port]' 'secret' 'username' 'password' <actions>
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):

	self.hostport = utils.stripquote(toklist[0])	# hostname:port
	self.secret = utils.stripquote(toklist[1])	# secret
	self.username = utils.stripquote(toklist[2])	# username
	self.password = utils.stripquote(toklist[3])	# password
	self.actionList = self.parseAction(toklist[4:])

	if ':' in self.hostport:
	    (self.host, self.port) = string.split( self.hostport, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.hostport
	    self.port = 1645


	# Set any directive-specific variables
	self.Action.varDict['radiushost'] = self.host
	self.Action.varDict['radiusport'] = self.port
	self.Action.varDict['radiussecret'] = self.secret
	self.Action.varDict['radiususername'] = self.username
	self.Action.varDict['radiuspassword'] = self.password

	# define the unique ID
	self.ID = '%s.RADIUS.%s.%d.%s' % (log.hostname,self.host,self.port,self.username)

	log.log( "<radius.py>RADIUS.tokenparser(): ID '%s' host '%s' port %d secret '%s' username '%s'" % (self.ID, self.host, self.port, self.secret, self.username), 8 )


    def docheck(self, Config):
	"""Perform a Radius authentication and return results."""

	log.log( "<radius.py>RADIUS.docheck(): host '%s' port %d username '%s'" % (self.host, self.port, self.username), 7 )

	timing = None

	# create pop3 connection object
	r = radcm.Radius( self.host, self.secret, self.port  )
	tstart = time.time()
	try:
	    z = r.authenticate(self.username,self.password)
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
	    log.log( "<radius.py>RADIUS.docheck(): timing could not be measured, setting to 0", 3 )

	# assign variables
	self.Action.varDict['radiustiming'] = timing

	log.log( "<radius.py>RADIUS.docheck(): timing=%s z=%s" % (timing,z), 8 )

	self.doAction(Config)

        Config.q.put( (self,time.time()+self.scanperiod) )      # put self back in the Queue


##
## END - radius.py
##
