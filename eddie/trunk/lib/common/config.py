## 
## File		: config.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Date		: 971211 
## 
## Description	: Eddie Software Config
##
## $Id$
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

# Python specific modules
import sys, string, os

# Eddie specific modules
import directive, definition, log, proc, utils, eddieElvin4


## Define exceptions
ParseFailure = 'ParseFailure'
#ParseNotcomplete = 'ParseNotcomplete'

############### DEFAULT SETTINGS ###################
##
## Scan Period in seconds (default is 10 minutes)
##
scanperiod = 10*60
scanperiodraw = '10m'

##
## Maximum number of threads Eddie will attempt to limit to.
## Set with NUMTHREADS in config.
##
num_threads = 10


##
## Default port to listen to console connections
##
consport=33343

####################################################


class Config:
    """The main Eddie configuration class."""

    def __init__(self, name, parent=None):
	if len(name) < 1:
	    raise SyntaxError

	self.name = name
	self.type = "Config"
	self.display = 0	# flag to indicate if we have displayed some info about the config (ie: only display it once)

    	# initialise our config lists/dicts
       	self.ruleList = directive.Rules()	# object which holds all rule definitions
	self.MDict = definition.MsgDict()	# object which holds all Message definitions
	if parent != None:
	    self.MDict.update(parent.MDict)	# inherit parent M-tree

	#self.defDict = {}			# dictionary of DEFinitions
	self.aliasDict = {}			# dictionary of ALIASes
	self.NDict = {}				# dictionary of Notification definitions
	self.classDict = {}			# dictionary of Class definitions

	self.groups = []
	self.configfiles = {}			# dictionary of config file mtimes

	# Inherit parent properties if given
	if parent != None:
	    self.parent = parent
	    #self.defDict.update(parent.defDict)
	    self.aliasDict.update(parent.aliasDict)
	    self.NDict.update(parent.NDict)
	    # TODO: copy ruleList and MDict too ?

    def __str__(self):
	"""Display Config in readable format (ie: for debugging)."""

	str = "<Config name='%s' type='%s'" % (self.name, self.type)
	str = str + "\n\n ruleList: %s" % self.ruleList
	str = str + "\n\n groups:"
	for i in self.groups:
	    str = str + " %s" % i
	str = str + "\n\n MDict:"
	for i in self.MDict.keys():
	    str = str + " %s" % self.MDict[i]
	#str = str + "\n\n defDict: %s" % self.defDict
	str = str + "\n\n aliasDict: %s" % self.aliasDict
        str = str + "\n\n NDict:"
	for i in self.NDict.keys():
	    str = str + " %s" % self.NDict[i]
        str = str + "\n\n classDict: %s" % self.classDict
        str = str + "\n>"
	return str

    def newgroup(self, toklist, toktypes, parent=None):
	"""Add new rules group."""

	# Require 3 tokens, ('group', <str>, ':')
	#if len(toklist) < 3:
	#    raise ParseNotcomplete
	
	# 3rd token must be a ':'
	if toklist[2] != ':':
	    raise ParseFailure, "Expected ':', found '%s'" % toklist[2]

	# group name (2nd token) should be text (ie: token type 'NAME')
	if toktypes[1] != 'NAME':
	    raise ParseFailure, "Unexpected group type, should be text"

	# Create new group
	newgroup = Config(toklist[1], parent)

	# If current host is a part of this group then add the group to the
	# list, otherwise don't bother - so the group will be parsed but will
	# not be kept.
	#if useGroup( log.hostname, toklist[1] ):
	# Add to group list

	# Add to parent's group list
	if parent != None:
	    parent.groups.append(newgroup)

	return newgroup


    def give(self, obj):
	"""Object 'obj' is given to Config, and placed in the appropriate list."""

	if obj.type == 'N':
	    self.NDict[obj.name] = obj
	elif obj.type == 'M':
	    self.MDict[obj.name] = obj
	elif obj.type == 'ALIAS':
	    self.aliasDict[obj.name] = obj.value
	elif obj.type == 'CLASS':
	    self.classDict[obj.name] = obj.hosts
	elif obj.type in directives.keys():
	    # add Rule to ruleList...
	    self.ruleList = self.ruleList + obj
	else:
	    #raise "Config.give(): Unknown object type %s" % obj
	    # Don't want any object that doesn't match above
	    return


    def checkfiles(self):
	"""Check if any of the config or rules files have been modified."""

	for f in self.configfiles.keys():
	    try:
		if os.stat(f)[8] != self.configfiles[f]:		# check mtime
		    return 1
	    except os.error:
		if sys.exc_value == 'Connection timed out':
		    # can happen when files on NFS mounted filesystem
		    log.log( "<config>Config.checkfiles(), Timeout while trying to stat '%s' - skipping file checks."%(f), 5 )
		    return 0

	return 0


    def getDirective(self, id):
	"""Return directive object with given id."""

	for d in self.ruleList.keys():
	    list = self.ruleList[d]
	    if list != None:
		for i in list:
		    if i.ID == id:
			return i

	return None


##
## The base configoption class.  Derive all config options from this base class.
##
class ConfigOption:
    def __init__(self, list, typelist):
	self.basetype = 'ConfigOption'	# the object can know its own basetype
	self.type = list[0]		# the config option type of this instance


##
## CONFIGURATION OPTIONS
##

## SCANPERIOD - the time (in seconds) to pause between checks
class SCANPERIOD(ConfigOption):
    def __init__( self, list, typelist ):

	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 or 4 elements ['SCANPERIOD', '=', <int>, [<char>,]] then raise an error
	if len(list) < 3 or len(list) > 4:
	    raise ParseFailure, "SCANPERIOD definition has %d tokens when expecting 3 or 4" % len(list)

	# ok, value is 3rd[+4th] list element
	if len(list) == 3:
	    value = list[2]
	else:
    	    value = list[2]+list[3]

	global scanperiodraw
	scanperiodraw = value			# keep the raw scanperiod
	value = utils.val2secs( value )		# convert value to seconds
	if value > 0:
	    global scanperiod
	    scanperiod = value			# set the config option
	log.log( "<config>SCANPERIOD(), scanperiod set to %s (%d seconds)." % (scanperiodraw, scanperiod), 8 )


## LOGFILE - where to store log messages
class LOGFILE(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['LOGFILE', '=', <val>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "LOGFILE definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	log.logfile = utils.stripquote(list[2])			# set the config option
	log.log( "<config>LOGFILE(), logfile set to '%s'." % (log.logfile), 8 )



## LOGLEVEL - how much logging to do
class LOGLEVEL(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['LOGLEVEL', '=', <val>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "LOGLEVEL definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	log.loglevel = string.atoi(list[2])		# set the config option
	log.log( "<config>LOGLEVEL(), loglevel set to %d" % (log.loglevel), 8 )



## ADMIN - email address of Eddie administrator
# only currently supports 1 email address
# TODO: support more than 1 email address...
class ADMIN(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['ADMIN', '=', <str>] then
	# raise an error
	if len(list) != 3:
	    raise ParseFailure, "ADMIN definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	log.adminemail = utils.stripquote(list[2])		# set the config option
	log.log( "<config>ADMIN(), admin set to '%s'." % (log.adminemail), 8 )


## ADMINLEVEL - how much logging to send to admin
class ADMINLEVEL(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['ADMINLEVEL', '=', <val>] then
	# raise an error
	if len(list) != 3:
	    raise ParseFailure, "ADMINLEVEL definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	log.adminlevel = string.atoi(list[2])		# set the config option
	log.log( "<config>ADMINLEVEL(), adminlevel set to '%d'." % (log.adminlevel), 8 )


## ADMIN_NOTIFY - how often to send admin-logs to admin
class ADMIN_NOTIFY(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 or 4 elements ['ADMIN_NOTIFY', '=', <int>, [<char>,]] then raise an error
	if len(list) < 3 or len(list) > 4:
	    raise ParseFailure, "ADMIN_NOTIFY definition has %d tokens when expecting 3 or 4" % len(list)

	# ok, value is 3rd[+4th] list element
	if len(list) == 3:
	    rawval = list[2]
	else:
	    rawval = list[2]+list[3]

	value = utils.val2secs( rawval )		# convert value to seconds
	if value > 0:
	    log.admin_notify = value		# set the config option
	log.log( "<config>ADMIN_NOTIFY(), admin_notify set to %s (%d seconds)." % (rawval, log.admin_notify), 8 )


## INTERPRETERS - define the list of interpreters
class INTERPRETERS(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['INTERPRETERS', '=', <str>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "INTERPRETERS definition has %d tokens when expecting 3" % len(list)

	value = utils.stripquote(list[2])
	proc.interpreters = string.split(value, ',')
	log.log( "<config>INTERPRETERS(), interpreters defined as '%s'." % (proc.interpreters), 8 )


## CLASS - define a class
class CLASS(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )


	# if we don't have at least 4 elements ['CLASS', '=', <str>, [',', <str>, ...] ]
	# then raise an error
	if len(list) < 3:
	    raise ParseFailure, "INTERPRETERS definition has %d tokens when expecting 3" % len(list)

	self.name = list[1]
	hosts = list[3:]			# pull hosts out
	hosts = string.join(hosts, '')		# join all arguments
	hosts = utils.stripquote(hosts)	# in case the arguments are in quotes (optional)
	self.hosts = string.split(hosts, ',')	# finally, split into list of hosts

	log.log( "<config>CLASS(), class created %s:%s." % (self.name,self.hosts), 8 )


## ELVINURL - URL of Elvin server
class ELVINURL(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['ELVINURL', '=', <str>] then
	# raise an error
	if len(list) != 3:
	    raise ParseFailure, "ELVINURL definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	eddieElvin4.ELVINURL = utils.stripquote(list[2])		# set the config option
	log.log( "<config>ELVINURL(), elvin url set to '%s'." % (eddieElvin4.ELVINURL), 8 )


## ELVINSCOPE - Scope of Elvin server
class ELVINSCOPE(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['ELVINSCOPE', '=', <str>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "ELVINSCOPE definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	eddieElvin4.ELVINSCOPE = utils.stripquote(list[2])		# set the config option
	log.log( "<config>ELVINSCOPE(), elvin scope set to '%s'." % (eddieElvin4.ELVINSCOPE), 8 )


## NUMTHREADS - limit thread creation
class NUMTHREADS(ConfigOption):
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['NUMTHREADS', '=', <int>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "NUMTHREADS definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	global num_threads
	num_threads = int(list[2])		# set the config option
	log.log( "<config>NUMTHREADS, num_threads set to '%d'." % (num_threads), 8 )

class CONSOLE_PORT(ConfigOption):
    """Set the tcp port to listen on for console connections"""

    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['CONSOLE_PORT', '=', <int>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "CONSOLE_PORT definition has %d tokens when expecting 3" % len(list)

	# ok, value is 3rd list element
	global consport
	try:
	    consport = int(list[2])		# set the config option
	except TypeError:			# must be integer
	    raise ParseFailure, "CONSOLE_PORT is not an integer, '%s'" % (list[2])

	if consport < 0:
	    raise ParseFailure, "CONSOLE_PORT must be a positive integer, %d" % (consport)

	log.log( "<config>CONSOLE_PORT, consport set to '%d'." % (consport), 8 )


class EMAIL_FROM(ConfigOption):
    """Set the From: address used by the email() action."""
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['EMAIL_FROM', '=', <string>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "EMAIL_FROM definition has %d tokens when expecting 3" % len(list)

        import action
	action.action.EMAIL_FROM = utils.stripquote(list[2])	# set value in action class

	log.log( "<config>EMAIL_FROM, email From: set to '%s'" % (action.action.EMAIL_FROM), 8 )


class EMAIL_REPLYTO(ConfigOption):
    """Set the From: address used by the email() action."""
    def __init__( self, list, typelist ):
	apply( ConfigOption.__init__, (self,list, typelist) )

	# if we don't have 3 elements ['EMAIL_REPLYTO', '=', <string>] then raise an error
	if len(list) != 3:
	    raise ParseFailure, "EMAIL_REPLYTO definition has %d tokens when expecting 3" % len(list)

        import action
	action.action.EMAIL_REPLYTO = utils.stripquote(list[2])	# set value in action class

	log.log( "<config>EMAIL_REPLYTO, email From: set to '%s'" % (action.action.EMAIL_REPLYTO), 8 )





def loadExtraDirectives( directivedir ):
    """Load extra directives from given directory.  Each file
    in this directory must be an importable (.py) Python module
    which contain directives (one or more) as classes."""

    oldsyspath = sys.path			# save sys.path
    sys.path = [directivedir,] + sys.path	# restrict module path
    extradirectives = os.listdir(directivedir)
    for m in extradirectives:
	if m[-3:] == ".py":			# only want ".py" files
	    mname = m[:-3]			# get module name
	    exec "import %s"%(mname)		# import module
	    exec "mobjs = dir(%s)"%(mname)	# list of module's objects
	    for o in mobjs:			# Cycle thru module's objects
		d = "%s.%s"%(mname,o)
		exec "dtype = type(%s)"%(d)	# Get object type
		if dtype == type(Config):	# only want "class" objects
		    exec "directives[o] = %s"%(d) # add to directives dict

    sys.path = oldsyspath		# restore module path

    #print "directives:",directives

    keywords.update(directives)		# add new directives to keywords table


##
## This is a list of known keywords we accept in Eddie config/rules files
##

## Just the directives
directives = {  
		"N"		: definition.N,
		"FS"		: directive.FS,
                "SP"		: directive.SP,
	  	"PID"		: directive.PID,
	  	"COM"		: directive.COM,
		"PROC"		: directive.PROC,
		"PORT"		: directive.PORT,
                "IF"		: directive.IF,
                "NET"		: directive.NET,
                "SYS"		: directive.SYS,
                "STORE"		: directive.STORE,
             }


## Just the definitions
definitions = {
		"M"		: definition.M,
		"MSG"		: definition.MSG,
		"ALIAS"		: definition.ALIAS,
              }

## Just the settings
settings = {
		"SCANPERIOD"	: SCANPERIOD,
		"LOGFILE"	: LOGFILE,
		"LOGLEVEL"	: LOGLEVEL,
		"ADMIN"		: ADMIN,
		"ADMINLEVEL"	: ADMINLEVEL,
		"ADMIN_NOTIFY"	: ADMIN_NOTIFY,
		"INTERPRETERS"	: INTERPRETERS,
		"CLASS"		: CLASS,
		"ELVINURL"	: ELVINURL,
		"ELVINSCOPE"	: ELVINSCOPE,
		"NUMTHREADS"	: NUMTHREADS,
		"CONSOLE_PORT"	: CONSOLE_PORT,
		"EMAIL_FROM"	: EMAIL_FROM,
		"EMAIL_REPLYTO"	: EMAIL_REPLYTO,
           }

## Join all the above dictionaries to make the total keywords dictionary
keywords = {}
keywords.update(directives)
keywords.update(definitions)
keywords.update(settings)

##
## END - config.py
##
