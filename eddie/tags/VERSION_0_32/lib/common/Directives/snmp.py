## 
## File		: snmp.py 
## 
## Author       : Dougal Scott <dwagon@connect.com.au>
## 
## Date		: 20020430
## 
## Description	: Directives for SNMP polling
##
## $Id$
##
##
########################################################################
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
#
# This uses pysnmp available from http://sourceforge.net/projects/pysnmp/
# as it requires no external libraries (such as net-snmp) to work.
#
# snmpresponse	- What SNMP returned
# snmpdelta     - Change in values since last call (useful for COUNTER types)
# snmplastresponse - The last SNMP response
#
# Configuration options:
# oid  - SNMP oid to poll. This has to be the full OID in numeric format.
#        SNMP tables are not traversed. What you see is what you get
#        Required argument
# community - The community string to use to get access to the SNMP 
#             Defaults to 'public'
# port - UDP Port to connect to on the host. Defaults to 161
# maxretry - Number of consecutive timeouts before we give up and assume there
#            is a problem
# host - Host running the SNMP server. Localhost by default.

import string
import log, directive

class SNMP(directive.Directive):
    """SNMP directive.

       Sample rules:

       SNMP foo:
	   host='alt1.domain.name'
	   oid='1.3.6.1.4.1.1872.2.1.1.6.0'
	   community='private'
	   rule='response > 0'
	   maxretry=10
           action=email('alert', 'Head for the lifeboats: %(snmpresponse)s')

    SNMP router_traffic:
	scanperiod='5m'
        host='10.0.0.1'
        oid='1.3.6.1.2.1.2.2.1.10.2, 1.3.6.1.2.1.2.2.1.16.2'
        community='special'
        rule='not failed'
        maxretry=10
        action=elvinrrd("net-router_BRI01", "ibytes=%(response1)s", "obytes=%(response2)s")
    """

    ############################################################################
    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )
	self.lastresponse=None
	self.errors=0

	try:
	    from pysnmp import session
	    self.session = session	# save pointer to module if import ok
	    from pysnmp import error
	    self.pysnmperror = error
	except ImportError:
	    raise directive.ParseFailure, "Cannot import pysnmp module - SNMP directive not available."


    ############################################################################
    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	try:
	    self.args.host		# hostname to poll
        except AttributeError:
	    self.args.host=log.hostname

	try:
	    self.args.rule		# the rule
        except AttributeError:
            raise directive.ParseFailure, "Rule not specified"

	# Build up a list of requested OIDs
	self.oidlist = []
	try:
	    self.args.oid		# the OID(s) argument
        except AttributeError:
            raise directive.ParseFailure, "oid argument not specified"
	else:
	    rawoids = string.split(self.args.oid, ',')
	    i = 1
	    for o in rawoids:
		# pysnmp requires a list of ints
		o = string.strip(o)
		self.defaultVarDict['oid%d'%i] = o	# store variable
		t = string.split(o, '.')
		transoid = []
		for n in t:
		    transoid.append(int(n))
		self.oidlist.append(transoid)
		i = i + 1

	try:
	    self.args.community		
        except AttributeError:
            self.args.community='public'	# Shame on you

	try:	# Number of consequetive retries before failing
	    self.args.maxretry		
	    self.args.maxretry=int(self.args.maxretry)
        except AttributeError:
            self.args.maxretry=5

	try:
	    self.args.port		
	    self.args.port=int(self.args.port)
        except AttributeError:
            self.args.port=161

	self.defaultVarDict['host'] = self.args.host
	self.defaultVarDict['port'] = self.args.port
	self.defaultVarDict['community'] = self.args.community
	self.defaultVarDict['oid'] = self.args.oid
	self.defaultVarDict['maxretry'] = self.args.maxretry
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.SNMP.%s.%s' % (log.hostname,self.args.host)
	self.state.ID = self.ID

	log.log( "<snmp>SNMP.tokenparser(): ID '%s' host '%s' rule '%s' oid=%s community=%s parsed" % (self.ID, self.args.host, self.args.rule, self.args.oid, self.args.community), 8 )

    ############################################################################
    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	# Initialize the data
	data = {}
	data['failed'] = 0

	# Perform the snmp
	s = self.session.session(self.args.host, self.args.community)
	s.port = self.args.port

	i = 1
	for oid in self.oidlist:
	    oid = s.encode_oid(oid)
	    question = s.encode_request('GETREQUEST', [oid], [])
	    try:
		answer = s.send_and_receive(question)
	    except self.session.error.NoResponse:	# If timeout dont panic
		log.log( "<snmp>SNMP.getData(): ID '%s': Timeout talking to host '%s' port %d" % (self.ID, self.args.host, self.args.port), 5 )
		self.errors = self.errors+1
		if self.errors >= self.args.maxretry:
		    # Too many failed snmp requests - cancel directive
		    raise directive.DirectiveError, "Too Many Retries: Failed %d times" % self.errors
		else:
		    data['failed'] = 1
		    return data
	    except self.pysnmperror.TransportError, msg:		# Problem establishing snmp connection
		log.log( "<snmp>SNMP.getData(): ID '%s': Transport error talking to host '%s' port %d, %s" % (self.ID, self.args.host, self.args.port, msg), 5 )
		self.errors = self.errors+1
		if self.errors >= self.args.maxretry:
		    # Too many failed snmp requests - cancel directive
		    raise directive.DirectiveError, "Too Many Retries: Failed %d times" % self.errors
		else:
		    data['failed'] = 1
		    return data
	    self.errors = 0

	    try:
	        (obj,val) = s.decode_response(answer)
	    except self.pysnmperror.BadRequestID, msg:
	        log.log( "<snmp>SNMP.getData(): ID '%s': BadRequestID exception, %s" % (self.ID, msg), 5 )
		data['failed'] = 1
		return data

	    resp = map(s.decode_value,val)

	    if len(self.oidlist) == 1:
		# if only one oid, data variable is just 'response'
		data['response'] = resp[0]
		log.log( "<snmp>SNMP.getData(): host '%s' response=%s" % (self.args.host,resp[0]), 8 )
	    else:
		# if multiple oids, data variables are responsen, n=1,2,...,n
		data['response%d'%i] = resp[0]
		log.log( "<snmp>SNMP.getData(): host '%s' response%d=%s" % (self.args.host,i,resp[0]), 8 )
	    i = i + 1


#	if self.lastresponse==None:	# First time through, just collect 
#	    self.lastresponse=resp[0]
#	    log.log( "<snmp>SNMP.getData(): ID '%s': Preloading values. Received %s" % (self.ID, resp[0]), 8 )
#	    return None			# dont evaluate rule this time
#
#	try:			# Not everything is an integer
#	    data['delta']=int(resp[0])-int(self.lastresponse)
#	except ValueError:
#	    data['delta']=None
#
#	data['lastresponse']=self.lastresponse
#	self.lastresponse=resp[0]

        return data


##
## END - snmp.py
##
