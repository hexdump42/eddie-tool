#!/opt/local/bin/python 
## 
## File		: directive.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971205 
## 
## Description	: 
##
## $Id$
##
##

import os, string, re, sys, socket, time
import action, definition, utils, log

# Define exceptions
ParseFailure = 'ParseFailure'

# Rules holds all the directives in a hash where the value of each key is the
# list of rules relating to that key.
class Rules:
    def __init__(self):
	self.hash = {}

    # Overload '+', eg: rules + directive_rule
    def __add__(self, new):
	try:
	    tl = self.hash[new.type]

	except KeyError:
	    self.hash[new.type] = []
	    tl = []

	tl.append(new)

	self.hash[new.type] = tl
	return(self)

    # Overload '[]', eg: fs_directive_list = rules['FS']
    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None

    def keys(self):
	return self.hash.keys()
    
    def delete(self, directive):
	del self.hash[directive]

    def __str__(self):
	#str = ""
	#for r in self.hash.keys():
	#    str = str + "%s\n" % self.hash[r]
	#return str
	return "%s" % self.hash


##
## The base directive class.  Derive all directives from this base class.
##
class Directive:
    def __init__(self, toklist):
	# Check toklist for valid tokens
	if len(toklist) < 2:		# need at least 2 tokens
	    raise ParseFailure, "Directive expected at least 3 tokens, found %d" % len(toklist)
	if toklist[-1] != ':':		# last token should be a ':'
	    raise ParseFailure, "Directive expected ':' but didn't find one"

	self.basetype = 'Directive'	# the object can know its own basetype
	self.type = toklist[0]		# the directive type of this instance

	self.Action = action.action()	# create new action instance
	self.Action.varDict = {}	# dictionary of variables used for emails etc

	self.actionList = []		# each directive will have a list of actions

	# Set up informational variables - these are common to all Directives
	#  %h = hostname
	self.Action.varDict['h'] = log.hostname

	#  %sys = command from a system() action
	#     TODO
	self.Action.varDict['sys'] = '[sys not yet defined]'

	#  %act = show list of actions taken preceded by "The following actions
	#         were taken:" if any were taken
	self.Action.varDict['act'] = '[act not yet defined]'

	#  %actnm = show list of actions taken (excluding email()'s) preceded by
	#         "The following actions were taken:" if any were taken
	self.Action.varDict['actnm'] = '[actnm not yet defined]'


    # Perform actions for a directive
    def doAction(self, Config):
	actionList = self.actionList

	# Replace Action definitions with the corresponding actions
	#actionList = definition.parseList( actionList, ADict )

	# Put quotes around arguments so we can use eval()
	#actionList = utils.quoteArgs( actionList )

	# Set the 'action' variables with the expanded action list
	self.Action.varDict['act'] = 'The following actions were attempted:\n'
	self.Action.varDict['actnm'] = 'The following (non-email) actions were attempted:\n'
	#TODO:
	#for a in actionList:
	#    self.Action.varDict['act'] = self.Action.varDict['act'] + '\t' + a + '\n'
	#    if a[:5] != 'email':
	#	self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '\t' + a + '\n'

	# Perform each action
	ret = None
	self.Action.actionReports = {}		# dict of actions and their return status
	for a in actionList:
	    sre = re.compile( "([A-Za-z0-9_]+)\(([A-Za-z0-9_.]+),?([0-9]?)\)" )
	    inx = sre.search( a )
	    if inx == None:
		#raise SyntaxError, "actionList regex error"
		# Assume we have a simple action call (rather than a
		# notification definition.
		self.Action.msg = None
		#print "calling: self.Action."+a
		ret = eval( 'self.Action.'+a )
		self.Action.actionReports[a] = ret
		if ret == None:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % a
		elif ret == 0:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % a
		else:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (a, ret)

	    else:
		notif = inx.group(1)
		msg = inx.group(2)
		level = inx.group(3)
		if level == None or level == '':
		    level = '0'

		#print ">>>> notif:",notif
		#print ">>>> msg:",msg
		#print ">>>> level:",level

		try:
		    afunc = Config.NDict[notif].levels[level]
		except KeyError:
		    #print "Eddie: Error in directive.py line 148: Config.NDict[notif].levels[level] - level=%d" % level
		    log.log( "<directive>doAction(), Error in directive.py line 148: Config.NDict[notif].levels[level] - level=%d" % level, 1 )
		else:
		    #print ">>>> afunc:",afunc

		    self.Action.notif = notif
		    self.Action.msg = msg
		    self.Action.level = level
		    self.Action.MDict = Config.MDict #TODO: move to init() ?

		    aList = utils.trickySplit( afunc[0], ',' )
		    # Put quotes around arguments so we can use eval()
		    aList = utils.quoteArgs( aList )
		    for aa in aList:
			#try:
			    # Call the action
			    log.log( "<directive>Directive, calling action '%s'" % (aa), 9 )
			    ret = eval( 'self.Action.'+aa )
			    self.Action.actionReports[aa] = ret
			    if ret == None:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % aa
			    elif ret == 0:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % aa
			    else:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (aa, ret)

			#except AttributeError:
			    # Not an action function ... error...
		    #	log.log( "<directive>Directive, Error, 'action.%s' is not a defined action, config line follows,\n%s\n" % (a,self.raw), 2 )
	#print "actionReports:",self.Action.actionReports


    ##
    ## parseAction(toklist)
    ##  Parses token list and returns a list of action call strings
    ##
    def parseAction(self, toklist):
	actstr = ""
	for t in toklist:
	    if t != '\012':
		actstr = actstr + t
	actlist = utils.trickySplit( actstr, ',' )
	return actlist


##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.filesystem = string.join(toklist[1:-1], '')	# the filesystyem to check


    def tokenparser(self, toklist, toktypes, indent):

	self.rule = utils.stripquote(toklist[0])	# the rule
	self.actionList = self.parseAction(toklist[1:])

	# Set any FS-specific variables
	#  fsf = filesystem
	#  fsrule = rule
	self.Action.varDict['fsf'] = self.filesystem
	self.Action.varDict['fsrule'] = self.rule

	log.log( "<FS> filesystem: '%s' rule: '%s' action: '%s'" % (self.filesystem, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>FS(), docheck(), fs '%s', rule '%s'" % (self.filesystem,self.rule), 7 )
	df = dlist[self.filesystem]
	if df == None:
	    log.log( "<directive>FS(), Error, no df with filesystem '%s'" % (self.filesystem), 2 )
	    return

	dfenv = {}			# environment for df rules execution
	dfenv['used'] = string.atoi(df.getUsed())
	dfenv['avail'] = string.atoi(df.getAvail())
	dfenv['capac'] = string.atoi(df.getPctused())
	# TODO : calculate deltas from history...
	dfenv['useddelta'] = string.atoi(df.getUsedDelta())
	dfenv['availdelta'] = string.atoi(df.getAvailDelta())
	dfenv['capacdelta'] = string.atoi(df.getPctusedDelta())

	self.parseRule()

	#print "used='%d', avail='%d', capac='%d', useddelta='%d', availdelta='%d', capacdelta='%d'" % (dfenv['used'],dfenv['avail'],dfenv['capac'],dfenv['useddelta'],dfenv['availdelta'],dfenv['capacdelta'])

	result = eval( self.rule, dfenv )

	if result != 0:
	    # assign variables
	    self.Action.varDict['fsused'] = df.getUsed()
	    self.Action.varDict['fsavail'] = df.getAvail()
	    self.Action.varDict['fscapac'] = df.getPctused()
	    self.Action.varDict['fssize'] = df.getSize()
	    self.Action.varDict['fsdf'] = "%s%s" % (dlist.dfheader,df)

	    # get '%fsls' details for this filesystem
    	    fsls = os.popen("ls -l %s" % (df.mountpt), 'r')
 
	    fsls_output = ""
    	    for line in fsls.readlines():
		fsls_output = fsls_output + line
	    
	    fsls.close()
	    self.Action.varDict['fsls'] = fsls_output
	


    	    log.log( "<directive>FS(), rule '%s' was false, calling doAction()" % (self.rule), 6 )
    	    self.doAction(Config)

    # Parse the rule line and replace/remove certain characters
    def parseRule(self):
	parsed = ""

	skipnext = 0			# flag to skip next character/s

	for i in range(len(self.rule)):
	    if skipnext > 0:
		skipnext = skipnext - 1
		continue

	    c = self.rule[i]

	    if c == '%':	# throw away '%'s - don't need em
		continue
	    elif c == '|':	# replace '|'s with 'or'
		parsed = parsed + ' or '
		continue
	    elif c == '&':	# replace '&'s with 'and'
		parsed = parsed + ' and '
		continue
	    elif i == len(self.rule)-1:	# break out of 'switch' if c is last character
		pass
	    elif ( string.lower(c) + string.lower(self.rule[i+1]) ) == 'mb':
		parsed = parsed + '000'
		skipnext = 1
		continue
	    elif ( string.lower(c) + string.lower(self.rule[i+1]) ) == 'gb':
		parsed = parsed + '000000'
		skipnext = 1
		continue
	    
	    parsed = parsed + c

	self.rule = parsed



class PID(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.pidfile = string.join(toklist[1:-1], '')	# the pid file to check for
	self.ruleDict = { 'EX' : None,
		          'PR' : None }


    def tokenparser(self, toklist, toktypes, indent):

	# Expect first token to be rule - one of self.ruleDict
	if toklist[0] not in self.ruleDict.keys():
	    raise ParseFailure, "PID found unexpected rule '%s'" % toklist[0]

	self.rule = toklist[0]			# the rule (EX or PR)
	self.actionList = self.parseAction(toklist[1:])

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.Action.varDict['pidf'] = self.pidfile

	log.log( "<PID> pidfile: '%s' rule: '%s' action: '%s'" % (self.pidfile, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>PID(), docheck(), pidfile '%s', rule '%s'" % (self.pidfile,self.rule), 7 )
	if self.rule == "EX":
	    # Check if pidfile exists
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), EX, pidfile '%s' not found" % (self.pidfile), 6 )
		self.doAction(Config)
	    else:
		log.log( "<directive>PID(), EX, pidfile '%s' found" % (self.pidfile), 8 )
		pidfile.close()

	elif self.rule == "PR":
	    # check if process pid found in pidfile is running - no alert if pidfile not found
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), PR, pidfile '%s' not found" % (self.pidfile), 6 )
	    else:
		log.log( "<directive>PID(), PR, pidfile '%s' found" % (self.pidfile), 8 )
		pid = pidfile.readline()
		pidfile.close()
		pid = string.strip(pid)
		# strip '\n' from pid string if necessary
		if pid[-1:] == '\n':
		    pid = pid[:-1]

		# Get rid of any other junk after pid
		pid = string.split(pid)[0]

		pid = int(pid)		# want it as an integer

		self.Action.varDict['pid'] = pid

		# Search for pid from process list
		if plist.pidExists( pid ) == 0:
		    # pid not found - to make sure, let's sleep a bit then check again
		    log.log( "<directive>PID(), PR, pid %s not in process list - sleeping and checking again..." % (pid), 8 )
		    time.sleep( 30 )
		    plist.refresh()		# force refresh of proc list
		    if plist.pidExists( pid ) == 0:
			# there is no process with pid == pid
			log.log( "<directive>PID(), PR, pid %s not in process list" % (pid), 6 )
			self.doAction(Config)
		    else:
			log.log( "<directive>PID(), PR, pid %s is in process list" % (pid), 8 )


	else:
	    # invalid rule
	    log.log( "<directive>PID(), Error, '%s' is not a valid PID rule, config line follows,\n%s\n" % (self.rule,self.raw), 2 )


class PROC(Directive):
    """Process checks."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.name = utils.stripquote(toklist[1])			# the daemon to check for
	self.daemon = utils.stripquote(toklist[1])		# the daemon to check for
	self.ruleDict = { 'NR' : self.NR,
		          'R'  : self.R,
			  'check' : self.check }


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse tokenized input."""

	# Expect first token to be rule
	if toklist[0] in self.ruleDict.keys():
	    # - either one of self.ruleDict
	    self.rule = self.ruleDict[toklist[0]]	# Set the rule
	elif toktypes[0] == 'STRING':
	    # - or a string containing a special check
	    self.rule = self.ruleDict['check']
	    self.checkstring = utils.stripquote(toklist[0])
	else:
	    raise ParseFailure, "PROC found unexpected rule '%s'" % toklist[0]

	self.actionList = self.parseAction(toklist[1:])

	# Set any PROC-specific variables
	#  %procp = the process name
	self.Action.varDict['procp'] = self.daemon
	#  %procpid = pid of process (ie: if found running for R rule)
	self.Action.varDict['procpid'] = '[pid not yet defined]'

	log.log( "<PROC> daemon: '%s' rule: '%s' action: '%s'" % (self.daemon, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform specified check."""

	log.log( "<directive>PROC(), docheck(), daemon '%s', rule '%s'" % (self.daemon,self.rule), 7 )
	self.rule(Config)


    def NR(self,Config):
	"""Call action if process is found to be NOT running."""

	if plist.procExists( self.daemon ) == 0:
	    # process not running - let's sleep a bit then check again to make sure
	    log.log( "<directive>NR(PROC) daemon not running, '%s' - sleeping before recheck..." % (self.daemon), 8 )
	    time.sleep( 30 )
	    plist.refresh()		# force refresh of proc list
	    if plist.procExists( self.daemon ) == 0:
		log.log( "<directive>NR(PROC) daemon not running, '%s'" % (self.daemon), 6 )
		self.doAction(Config)


    def R(self,Config):
	"""Call action if process is found to BE running."""

	if plist.procExists( self.daemon ) > 0:
	    log.log( "<directive>R(PROC) daemon is running, '%s'" % (self.daemon), 6 )
	    # Set %procpid variable.
	    self.Action.varDict['procpid'] = plist[self.daemon].pid
	    self.doAction(Config)


    def check(self,Config):
	"""Executes a check string supplied by user."""

	try:
	    procenv = plist[self.daemon].procinfo()		# get dictionary of process details
	except AttributeError:
	    log.log( "<directive>PROC.check() warning, no process '%s'." % (self.daemon), 8 )
	    return

	result = eval( self.checkstring, procenv )

	if result != 0:
	    # build varDict from procenv
	    for i in procenv.keys():
		self.Action.varDict['proc%s'%(i)] = procenv[i]
	    self.doAction(Config)



class SP(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	# Must be 5 tokens to make up: ['SP', 'proto', '/', 'port', ':']
	if len(toklist) < 5:
	    raise ParseError, "SP proto/port not specified correctly"
	if toklist[2] != '/':
	    raise ParseError, "SP proto/port not specified correctly"

	self.proto = toklist[1]		# the proto to check
	self.port_n = toklist[3]	# the port to check


    def tokenparser(self, toklist, toktypes, indent):

	self.addr   = toklist[0]			# the addr to check
	self.actionList = self.parseAction(toklist[1:])

	# lets try resolving this service port to a number
	try:
	    self.port = socket.getservbyname(self.port_n, self.proto)
	    # print p
	except socket.error:
	    self.port = self.port_n

	self.Action.varDict['spport'] = self.port_n
	self.Action.varDict['spaddr'] = self.addr
	self.Action.varDict['spprot'] = self.proto

	log.log( "<Directive>SP, proto '%s', port '%s', bind addr '%s', action '%s'" % (self.proto, self.port, self.addr, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>SP(), docheck(), proto '%s', port '%s', addr '%s'" % (self.proto,self.port_n,self.addr), 7 )

	ret = nlist.portExists(self.proto, self.port, self.addr) != None
	if ret != 0:
	    log.log( "<directive>SP(), port %s/%s listener found bound to %s" % (self.proto , self.port_n, self.addr), 8 )
	else:
	    self.doAction(Config)
	    log.log( "<directive>SP(), port %s/%s no listener found bound to %s" % (self.proto , self.port_n, self.addr), 6 )


class COM(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.command = utils.stripquote(toklist[1])	# the command
	self.rule = None


    def tokenparser(self, toklist, toktypes, indent):
	toklist = toklist[:-1]		# lose CR
	toktypes = toktypes[:-1]	# lose CR

	if self.rule == None:
	    self.rule = utils.stripquote(toklist[0])
	    toklist = toklist[1:]

	if len(toklist) > 0:
	    self.actionList = self.actionList + self.parseAction(toklist)

	#self.rule = utils.stripquote(toklist[0])	# the rule
	#self.actionList = self.parseAction(toklist[1:])	# the action

	# Set any PID-specific variables
	#  %com = the command
	#  %rule = the rule
	self.Action.varDict['com'] = self.command
	self.Action.varDict['rule'] = self.rule

	log.log( "<COM> command: '%s' rule: '%s' action: '%s'" % (self.command, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>COM(), docheck(), command '%s', rule '%s'" % (self.command,self.rule), 7 )
	tmpprefix = "/var/tmp/com%d" % os.getpid()
	cmd = "%s >%s.out 2>%s.err" % (self.command, tmpprefix, tmpprefix )
	log.log( "<directive>COM.docheck(), calling system('%s')" % (cmd), 8 )
	retval = os.system( cmd )
	try:
	    outf = open( tmpprefix + ".out", 'r' )
	except IOError:
	    # stdout tmp file not found
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".out"), 2 )
	else:
	    out = outf.readline()
	    outf.close()
	    os.remove( tmpprefix + ".out" )
	    out = string.strip(out)
	    if out[-1:] == '\n':
		out = out[:-1]

	try:
	    errf = open( tmpprefix + ".err", 'r' )
	except IOError:
	    # stderr tmp file not found
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".err"), 2 )
	else:
	    err = errf.readline()
	    errf.close()
	    os.remove( tmpprefix + ".err" )
	    err = string.strip(err)
	    if err[-1:] == '\n':
		err = err[:-1]

        log.log( "<directive>COM.docheck(), retval=%d" % retval, 8 )
	log.log( "<directive>COM.docheck(), stdout='%s'" % out, 8 )
	log.log( "<directive>COM.docheck(), stderr='%s'" % err, 8 )

	# save values in variable dictionary
	self.Action.varDict['comout'] = out
	self.Action.varDict['comerr'] = err
	self.Action.varDict['comret'] = retval

        comenv = {}                      # environment for com rules execution
        comenv['out'] = out
        comenv['err'] = err
        comenv['ret'] = retval
	result=None
	try:
	    result = eval( self.rule, comenv )
	except:
	    #print "COM.docheck() : an error occured with rule '%s' - env was: %s"%(self.rule,comenv)
	    log.log( "<directive>COM.docheck() : an error occured with rule '%s' exception type: '%s' exception value: '%s' - env was: %s"%(self.rule,sys.exc_type,sys.exc_value,comenv), 3 )
	    return

        log.log( "<directive>COM.docheck(), eval:'%s', result='%s'" % (self.rule,result), 9 )
	if result != 0:
	    self.doAction(Config)


class PORT(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	# Expect only 3 tokens: ( 'PORT', <host>, ':' )
	if len(toklist) > 3:
	    raise ParseFailure, "Too many tokens for PORT directive"

	self.host = utils.stripquote(toklist[1])	# the host
	self.port = None
	self.sendstr = None
	self.expect = None


    def tokenparser(self, toklist, toktypes, indent):
	toklist = toklist[:-1]		# lose CR
	toktypes = toktypes[:-1]	# lose CR

	while len(toklist) > 0:
	    if self.port == None:
		try:
		    self.port = int(utils.stripquote(toklist[0]))
		except ValueError:
		    raise ParseFailure, "Port should be integer, found '%s'" % toklist[0]
    		toklist = toklist[1:]
	    elif self.sendstr == None:
		self.sendstr = utils.stripquote(toklist[0])
    		toklist = toklist[1:]
	    elif self.expect == None:
		self.expect = utils.stripquote(toklist[0])
    		toklist = toklist[1:]
	    else:
		self.actionList = self.actionList + self.parseAction(toklist)
    		toklist = []

	# Set any PORT-specific variables
	#  %porthost = the host
	#  %portport = the port
	#  %portsend = the send string
	#  %portexpect = the expect string
	#  %portrecv = the string received from port connection (at check time)
	self.Action.varDict['porthost'] = self.host
	self.Action.varDict['portport'] = self.port
	self.Action.varDict['portsend'] = self.sendstr
	self.Action.varDict['portexpect'] = self.expect
	self.Action.varDict['portrecv'] = ''

	log.log( "<directive>PORT parsed, host: '%s' port: '%d' sendstr: '%s' expect: '%s'" % (self.host, self.port, self.sendstr, self.expect), 8 )


    def docheck(self, Config):
	log.log( "<directive>PORT.docheck(), host '%s', port '%d', sendstr '%s', expect '%s'" % (self.host,self.port,self.sendstr,self.expect), 7 )

	self.Action.varDict['portrecv'] = ''

        if not self.isalive(host=self.host,port=self.port,send=self.sendstr,expect=self.expect):
	    log.log( "<directive>PORT.docheck(), isalive() failed.", 7 )
            self.doAction(Config)

    def isalive(self,host,port,send="",expect=""):
        """ Connects to host:port, sends send,
            receives input, compares it to expect
            and returns TRUE or FALSE accordingly """
        #print "Trying to connect to %s:%d send:'%s' exp:'%s'" % (host,port,send,expect)   #DEBUG
        try:
            try:
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect(host,port)
                if expect == "":
                    s.close()
                    return 1    # port connection ok
                else:
                    exec( "send='%s'" % send )
                    s.send(send)
                    data=s.recv(111024)
                    self.Action.varDict['portrecv'] = data

                    if data==expect or re.search( '.*' + expect + '.*', data, ) != None:
                        s.close()
                        return 1
                    else:
                        return 0
            finally:
                try:
                    s.close()
                except: 
                    pass
        except:
            return 0

	return 0
        # print isalive(host='daidyai.off.connect.com.au',port=50006,send='blah',expect='ALIVE')



class IF(Directive):
    """Network Interface directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	# Must be 3 tokens to make up: ['SP', 'ifname', ':']
	if len(toklist) != 3:
	    raise ParseError, "IF parse error, expected 3 tokens, found %d" % (len(toklist))
	if toklist[2] != ':':
	    raise ParseError, "IF parse error, no colon"

	self.name = utils.stripquote(toklist[1])		# the interface name
	self.rule = None
	self.checkstring = ''

        self.ruleDict = { 'NE' : self.NE,
			  'EX' : self.EX,
			  'check' : self.check }



    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""

	# Expect first token to be rule
        if toklist[0] in self.ruleDict.keys():
            # - either one of self.ruleDict
            self.rule = self.ruleDict[toklist[0]]       # Set the rule
        elif toktypes[0] == 'STRING':
            # - or a string containing a special check
            self.rule = self.ruleDict['check']
            self.checkstring = utils.stripquote(toklist[0])
        else:
            raise ParseFailure, "IF found unexpected rule '%s'" % toklist[0]

	self.actionList = self.parseAction(toklist[1:])

	self.Action.varDict['ifname'] = self.name
	self.Action.varDict['ifrule'] = self.rule
	self.Action.varDict['ifcheckstring'] = self.checkstring

	log.log( "<Directive>IF, name '%s', rule '%s', checkstring '%s', action '%s'" % (self.name, self.rule, self.checkstring, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>IF(), docheck(), name '%s', check '%s', checkstring '%s'" % (self.name,self.check,self.checkstring), 7 )

	self.rule(Config)


    def NE(self, Config):
	"""Check that an interface currently does not exist."""

	if nlist.getInterface(self.name) == None:
	    # interface doesn't exist
	    log.log( "<directive>IF.NE() interface '%s' does not exist" % (self.name), 6 )
	    self.doAction(Config)


    def EX(self, Config):
	"""Check that an interface currently exists."""

	if nlist.getInterface(self.name) != None:
	    # interface exists
	    log.log( "<directive>IF.EX() interface '%s' exists" % (self.name), 6 )
	    self.doAction(Config)


    def check(self, Config):
	"""Execute a check supplied by the user as a string."""

	i = nlist.getInterface(self.name)
	if i == None:
	    log.log( "<directive>IF.check() warning, no interface '%s'." % (self.name), 8 )
	    return		# ignore if this interface doesn't exist

	ifenv = i.ifinfo()	# get dictionary of interface details

	result = eval( self.checkstring, ifenv )

	if result != 0:
	    # build varDict from ifenv
	    for i in ifenv.keys():
		self.Action.varDict['if%s'%(i)] = ifenv[i]
	    self.doAction(Config)
	


class NET(Directive):
    """Network Statistics directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	# Must be 2 tokens to make up: ['NET', ':']
	if len(toklist) != 2:
	    raise ParseError, "NET parse error, expected 2 tokens, found %d" % (len(toklist))
	if toklist[1] != ':':
	    raise ParseError, "NET parse error, no colon"

	self.rulestring = ''


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""

	# Expect first token to be rule (a string)
        if toktypes[0] != 'STRING':
	    raise ParseError, "NET parse error, rule is not string."

	self.rulestring = utils.stripquote(toklist[0])

	self.actionList = self.parseAction(toklist[1:])

	self.Action.varDict['netrule'] = self.rulestring

	log.log( "<Directive>NET, rule '%s', action '%s'" % (self.rulestring, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>NET(), docheck(), rulestring '%s'" % (self.rulestring), 7 )

	netenv = nlist.statstable.hash	# get dictionary of network stats

	result = eval( self.rulestring, netenv )

	if result != 0:
	    # build varDict from netenv
	    for i in netenv.keys():
		self.Action.varDict['net%s'%(i)] = netenv[i]
	    self.doAction(Config)



##
## END - directive.py
##


##
## END - directive.py
##
