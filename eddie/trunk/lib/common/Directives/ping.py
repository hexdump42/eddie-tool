## 
## File		: ping.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 20010710
## 
## Description	: Directives for network pinging
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


# Imports: ping modules
import pinger
# Imports: Python
import socket
# Imports: Eddie
import log, directive



## Directives ##


class PING(directive.Directive):
    """PING directive.  Ping a host.

       Sample rule:
       PING foo: host="foo.domain.name"
                 rule="!alive"
                 action="email('alert', 'host foo is not responding to pings')"

       Optional arguments:
	numpings=<int>	# number of times to ping, default is 5
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.host		# hostname to ping
        except AttributeError:
            raise directive.ParseFailure, "Host not specified"
	try:
	    self.args.rule		# the rule
        except AttributeError:
            raise directive.ParseFailure, "Rule not specified"

	try:
	    self.args.numpings		# number of times to ping
	    self.args.numpings = int(self.args.numpings)	# must be int
	    if self.args.numpings < 1:
		raise directive.ParseFailure, "Numpings must be > 1, not %d" % (self.args.numpings)
        except ValueError:
	    raise directive.ParseFailure, "Numpings must be an integer, not '%s'" % (self.args.numpings)
        except AttributeError:
            self.args.numpings=5	# Default is 5 pings

	# Set variables for Actions to use
	self.Action.varDict['pinghost'] = self.args.host
	self.Action.varDict['pingnumpings'] = self.args.numpings
	self.Action.varDict['pingrule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.PING.%s.%s' % (log.hostname,self.args.host)
	self.state.ID = self.ID

	log.log( "<ping>PING.tokenparser(): ID '%s' host '%s' rule '%s' numpings=%d" % (self.ID, self.args.host, self.args.rule, self.args.numpings), 8 )


    def docheck(self, Config):
	"""Ping a host a number of times and evaluate rule.
	"""

	log.log( "<ping>PING.docheck(): ID '%s' host '%s' rule '%s' numpings=%d" % (self.ID, self.args.host, self.args.rule, self.args.numpings), 7 )

	# Perform the pinging
	try:
	    p = pinger.Pinger( self.args.host, self.args.numpings )
	except socket.error, err:
	    log.log( "<ping>PING.docheck(): Socket Error, host '%s', %s" % (self.args.host,err), 4 )
	    self.putInQueue( Config.q )     # put self back in the Queue
	    return 1

	p.ping()
	s = p.get_summary()
	# Summary is 6-tuple:
	# (min round-trip time ms (int),
	#  avg round-trip time ms (int),
	#  max round-trip time ms (int),
	#  num packets transmitted (int),
	#  nun packets received (int),
	#  packet loss (float)
	# )
	# eg: (0, 0, 1, 3, 3, 0.0)

	# assign variables (see above)
	self.Action.varDict['pingmintriptime'] = s[0]
	self.Action.varDict['pingavgtriptime'] = s[1]
	self.Action.varDict['pingmaxtriptime'] = s[2]
	self.Action.varDict['pingnumpktstx'] = s[3]
	self.Action.varDict['pingnumpktsrx'] = s[4]
	self.Action.varDict['pingpktloss'] = s[5] * 100		# convert to %

	log.log( "<ping>PING.docheck(): host '%s' pingmintriptime=%d pingavgtriptime=%d pingmaxtriptime=%s pingnumpktstx=%d pingnumpktsrx=%d pingpktloss=%f" % (self.args.host,s[0],s[1],s[2],s[3],s[4],s[5]), 8 )

	# Evaluate Rule
        rulesenv = {}                   # environment for rules execution
        rulesenv['mintriptime'] = s[0]
        rulesenv['avgtriptime'] = s[1]
        rulesenv['maxtriptime'] = s[2]
        rulesenv['numpktstx'] = s[3]
        rulesenv['numpktsrx'] = s[4]
        rulesenv['pktloss'] = s[5] * 100		# convert to %
	if s[4] == 0:	# if no packets received, define alive to be false
	    rulesenv['alive'] = 0
	else:
	    rulesenv['alive'] = 1

        result = eval( self.args.rule, rulesenv )

        if result == 0:
            self.state.stateok(Config)    # update state info for check passed

	else:
	    self.state.statefail()	# set state to fail before calling doAction()
	    self.doAction(Config)

        self.putInQueue( Config.q )     # put self back in the Queue



##
## END - ping.py
##
