## 
## File		: ping.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20010710
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


##
## Directives
##
class PING(directive.Directive):
    """
    PING directive.  Includes facilities to ping remote hosts and perform
    checks based on:
    - whether the host is alive or not;
    - percentage of ping responses successful;
    - ping rount-trip-times.

    Sample rule:
       PING foo: host="foo.domain.name"
                 rule="not alive"
                 action="email('alert', 'host foo is not responding to pings')"

    Optional arguments:
	numpings=<int>	# number of times to ping, default is 5
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
	self.defaultVarDict['host'] = self.args.host
	self.defaultVarDict['numpings'] = self.args.numpings
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.PING.%s.%s' % (log.hostname,self.args.host)
	self.state.ID = self.ID

	log.log( "<ping>PING.tokenparser(): ID '%s' host '%s' rule '%s' numpings=%d" % (self.ID, self.args.host, self.args.rule, self.args.numpings), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.

	Ping a host a set number of times and record number of successful
	responses and round-trip-time stats (min/max and average).
	"""

	# Perform the pinging
	try:
	    p = pinger.Pinger( self.args.host, self.args.numpings )
	except socket.error, err:
	    log.log( "<ping>PING.getData(): Socket Error, host '%s', %s" % (self.args.host,err), 5 )
	    return None

	p.ping()
	s = p.get_summary()
	# Summary is 6-tuple:
	# (min round-trip time sec (float),
	#  avg round-trip time sec (float),
	#  max round-trip time sec (float),
	#  num packets transmitted (int),
	#  nun packets received (int),
	#  packet loss (float)
	# )
	# eg: (0, 0, 1, 3, 3, 0.0)

	# assign variables (see above)
	data = {}
	data['mintriptime'] = s[0]
	data['avgtriptime'] = s[1]
	data['maxtriptime'] = s[2]
	data['numpktstx'] = s[3]
	data['numpktsrx'] = s[4]
	data['pktloss'] = s[5] * 100		# convert to %

	log.log( "<ping>PING.getData(): host '%s' mintriptime=%d avgtriptime=%d maxtriptime=%s numpktstx=%d numpktsrx=%d pktloss=%f" % (self.args.host,s[0],s[1],s[2],s[3],s[4],s[5]), 7 )

	if s[4] == 0:	# if no packets received, define alive to be false
	    data['alive'] = 0
	else:
	    data['alive'] = 1

	return data


##
## END - ping.py
##
