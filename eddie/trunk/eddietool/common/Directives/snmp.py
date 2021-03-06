
'''
File                : snmp.py 

Start Date        : 20020430

Description        : Directives for SNMP polling
  This uses pysnmp available from http://sourceforge.net/projects/pysnmp/
  as it requires no external libraries (such as net-snmp) to work.
 
  snmpresponse        - What SNMP returned
  snmpdelta     - Change in values since last call (useful for COUNTER types)
  snmplastresponse - The last SNMP response
 
  Configuration options:
  oid  - SNMP oid to poll. This has to be the full OID in numeric format.
         SNMP tables are not traversed. What you see is what you get
         Required argument
  community - The community string to use to get access to the SNMP 
              Defaults to 'public'
  port - UDP Port to connect to on the host. Defaults to 161
  maxretry - Number of consecutive timeouts before we give up and assume there
             is a problem
  host - Host running the SNMP server. Localhost by default.

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

__author__ = 'Dougal Scott'

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


import string
from eddietool.common import log, directive

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

       # Now supports 64-bit counter split into high/low OIDs.  Specify these
       # as "OIDhigh:OIDlow".
       SNMP router_traffic_64bit:
           scanperiod='5m'
           host='10.0.0.1'
           oid='1.3.6.1.2.1.2.2.1.10.2:1.3.6.1.2.1.2.2.1.10.3, 1.3.6.1.2.1.2.2.1.16.2:1.3.6.1.2.1.2.2.1.16.3'
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
            from eddietool.common.Extra.pysnmp import session
            self.session = session        # save pointer to module if import ok
            from eddietool.common.Extra.pysnmp import error
            self.pysnmperror = error
        except ImportError:
            raise directive.ParseFailure, "Cannot import pysnmp module - SNMP directive not available."


    ############################################################################
    def tokenparser(self, toklist, toktypes, indent):
        apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

        try:
            self.args.host                # hostname to poll
        except AttributeError:
            self.args.host=log.hostname

        try:
            self.args.rule                # the rule
        except AttributeError:
            raise directive.ParseFailure, "Rule not specified"

        # Build up a list of requested OIDs
        self.oidlist = []
        try:
            self.args.oid                # the OID(s) argument
        except AttributeError:
            raise directive.ParseFailure, "oid argument not specified"
        else:
            rawoids = string.split(self.args.oid, ',')
            i = 1
            for o in rawoids:
                # pysnmp requires a list of ints
                o = string.strip(o)
                self.defaultVarDict['oid%d'%i] = o        # store variable

                # chris 2003-05-03: support for 64bit (high/low) counters
                if ':' in o:
                    (highoid,lowoid) = string.split(o, ':')
                    th = string.split(highoid, '.')
                    tl = string.split(lowoid, '.')
                    transoidh = []
                    for n in th:
                        transoidh.append(int(n))
                    transoidl = []
                    for n in tl:
                        transoidl.append(int(n))
                    self.oidlist.append( (transoidh,transoidl) )        # add high/low OIDs

                else:
                    # standard OIDs
                    t = string.split(o, '.')
                    transoid = []
                    for n in t:
                        transoid.append(int(n))
                    self.oidlist.append(transoid)

                i = i + 1

        try:
            self.args.community                
        except AttributeError:
            self.args.community='public'        # Shame on you

        try:        # Number of consequetive retries before failing
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
        for eachoid in self.oidlist:
            # chris 2003-05-03: support for 64bit (high/low) counters
            if type(eachoid) == type(()):        # high/low OID tuple
                oids = eachoid
                highlow = 1
            else:
                oids = (eachoid,)
                highlow = 0

            for oid in oids:
                oid = s.encode_oid(oid)
                question = s.encode_request('GETREQUEST', [oid], [])
                try:
                    answer = s.send_and_receive(question)
                except self.session.error.NoResponse:        # If timeout dont panic
                    log.log( "<snmp>SNMP.getData(): ID '%s': Timeout talking to host '%s' port %d" % (self.ID, self.args.host, self.args.port), 5 )
                    self.errors = self.errors+1
                    if self.errors >= self.args.maxretry:
                        # Too many failed snmp requests - cancel directive
                        raise directive.DirectiveError, "Too Many Retries: Failed %d times" % self.errors
                    else:
                        data['failed'] = 1
                        return data
                except self.pysnmperror.TransportError, msg:                # Problem establishing snmp connection
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

                if highlow:
                    if highlow == 1:
                        largeoid = pow(2,32) * resp[0]
                        highlow = 2
                    else:
                        largeoid = largeoid + resp[0]

            if highlow:
                result = largeoid
            else:
                result = resp[0]

            if len(self.oidlist) == 1:
                # if only one oid, data variable is just 'response'
                data['response'] = result
                log.log( "<snmp>SNMP.getData(): host '%s' response=%s" % (self.args.host,result), 8 )
            else:
                # if multiple oids, data variables are responsen, n=1,2,...,n
                data['response%d'%i] = result
                log.log( "<snmp>SNMP.getData(): host '%s' response%d=%s" % (self.args.host,i,result), 8 )
            i = i + 1


#        if self.lastresponse==None:        # First time through, just collect 
#            self.lastresponse=resp[0]
#            log.log( "<snmp>SNMP.getData(): ID '%s': Preloading values. Received %s" % (self.ID, resp[0]), 8 )
#            return None                        # dont evaluate rule this time
#
#        try:                        # Not everything is an integer
#            data['delta']=int(resp[0])-int(self.lastresponse)
#        except ValueError:
#            data['delta']=None
#
#        data['lastresponse']=self.lastresponse
#        self.lastresponse=resp[0]

        return data


##
## END - snmp.py
##
