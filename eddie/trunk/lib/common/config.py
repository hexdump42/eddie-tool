#!/opt/local/bin/python 
## 
## File		: config.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971211 
## 
## Description	: Eddie Software Config
##
## $Id$
##

# Python specific modules
import sys, string, regex, os

# Eddie specific modules
import directive, definition, log, proc, utils, eddieElvin


## Define exceptions
ParseFailure = 'ParseFailure'
ParseNotcomplete = 'ParseNotcomplete'

##
## Scan Period in seconds (default is 10 minutes)
##
scanperiod = 10*60
scanperiodraw = '10m'


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

	self.defDict = {}			# dictionary of DEFinitions
	self.NDict = {}				# dictionary of Notification definitions
	self.classDict = {}			# dictionary of Class definitions

	self.groups = []
	self.configfiles = {}			# dictionary of config file mtimes

	# Inherit parent properties if given
	if parent != None:
	    self.parent = parent
	    self.defDict.update(parent.defDict)
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
	str = str + "\n\n defDict: %s" % self.defDict
        str = str + "\n\n NDict:"
	for i in self.NDict.keys():
	    str = str + " %s" % self.NDict[i]
        str = str + "\n\n classDict: %s" % self.classDict
        str = str + "\n>"
	return str

    def newgroup(self, toklist, toktypes, parent=None):
	"""Add new rules group."""

	# Require 3 tokens, ('group', <str>, ':')
	if len(toklist) < 3:
	    raise ParseNotcomplete
	
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
	elif obj.type == 'DEF':
	    self.defDict[obj.name] = obj.text
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
		    log.log( "<Config>Checkfiles(), Timeout while trying to stat '%s' - skipping file checks."%(f), 4 )
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
    def __init__(self, list):
	self.basetype = 'ConfigOption'	# the object can know its own basetype
	self.type = list[0]		# the config option type of this instance


##
## CONFIGURATION OPTIONS
##

## SCANPERIOD - the time (in seconds) to pause between checks
class SCANPERIOD(ConfigOption):
    def __init__( self, list ):

	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 or 5 elements ['SCANPERIOD', '=', <int>, [<char>,] '012'] then
	# raise an error
	if len(list) < 4 or len(list) > 5:
	    raise ParseFailure, "SCANPERIOD definition has %d tokens when expecting 4 or 5" % len(list)

	# ok, value is 3rd[+4th] list element
	if len(list) == 4:
	    value = list[2]
	else:
    	    value = list[2]+list[3]

	global scanperiodraw
	scanperiodraw = value			# keep the raw scanperiod
	value = utils.val2secs( value )		# convert value to seconds
	if value > 0:
	    global scanperiod
	    scanperiod = value			# set the config option
	log.log( "<Config>SCANPERIOD(), scanperiod set to %s (%d seconds)." % (scanperiodraw, scanperiod), 6 )


## LOGFILE - where to store log messages
class LOGFILE(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['LOGFILE', '=', <val>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "LOGFILE definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	log.logfile = utils.stripquote(list[2])			# set the config option
	log.log( "<Config>LOGFILE(), logfile set to '%s'." % (log.logfile), 6 )



## LOGLEVEL - how much logging to do
class LOGLEVEL(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['LOGLEVEL', '=', <val>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "LOGLEVEL definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	log.loglevel = string.atoi(list[2])		# set the config option



## ADMIN - email address of Eddie administrator
# only currently supports 1 email address
# TODO: support more than 1 email address...
class ADMIN(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['ADMIN', '=', <str>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "ADMIN definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	log.adminemail = utils.stripquote(list[2])		# set the config option
	log.log( "<Config>ADMIN(), admin set to '%s'." % (log.adminemail), 6 )


## ADMINLEVEL - how much logging to send to admin
class ADMINLEVEL(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['ADMINLEVEL', '=', <val>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "ADMINLEVEL definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	log.adminlevel = string.atoi(list[2])		# set the config option
	log.log( "<Config>ADMINLEVEL(), adminlevel set to '%d'." % (log.adminlevel), 6 )


## ADMIN_NOTIFY - how often to send admin-logs to admin
class ADMIN_NOTIFY(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 or 5 elements ['ADMIN_NOTIFY', '=', <int>, [<char>,] '012'] then
	# raise an error
	if len(list) < 4 or len(list) > 5:
	    raise ParseFailure, "ADMIN_NOTIFY definition has %d tokens when expecting 4 or 5" % len(list)

	# ok, value is 3rd[+4th] list element
	if len(list) == 4:
	    rawval = list[2]
	else:
	    rawval = list[2]+list[3]

	value = utils.val2secs( rawval )		# convert value to seconds
	if value > 0:
	    log.admin_notify = value		# set the config option
	log.log( "<Config>ADMIN_NOTIFY(), admin_notify set to %s (%d seconds)." % (rawval, log.admin_notify), 6 )


## INTERPRETERS - define the list of interpreters
class INTERPRETERS(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['INTERPRETERS', '=', <str>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "INTERPRETERS definition has %d tokens when expecting 4" % len(list)

	value = utils.stripquote(list[2])
	proc.interpreters = string.split(value, ',')
	log.log( "<Config>INTERPRETERS(), interpreters defined as '%s'." % (proc.interpreters), 6 )


## CLASS - define a class
class CLASS(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have at least 4 elements ['CLASS', '=', <str>, [',', <str>, ...] '\012']
	# then raise an error
	if len(list) < 4:
	    raise ParseFailure, "INTERPRETERS definition has %d tokens when expecting 4" % len(list)

	self.name = list[1]
	hosts = list[3:-1]			# pull hosts out
	hosts = string.join(hosts, '')		# join all arguments
	hosts = utils.stripquote(hosts)	# in case the arguments are in quotes (optional)
	self.hosts = string.split(hosts, ',')	# finally, split into list of hosts

	log.log( "<Config>CLASS(), class created %s:%s." % (self.name,self.hosts), 8 )


## ELVINHOST - hostname or address of Elvin server
class ELVINHOST(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['ELVINHOST', '=', <str>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "ELVINHOST definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	eddieElvin.ELVINHOST = utils.stripquote(list[2])		# set the config option
	log.log( "<Config>ELVINHOST(), elvin host set to '%s'." % (eddieElvin.ELVINHOST), 6 )


## ELVINPORT - tcp port of Elvin server
class ELVINPORT(ConfigOption):
    def __init__( self, list ):
	apply( ConfigOption.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 4 elements ['ELVINPORT', '=', <int>, '012'] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "ELVINPORT definition has %d tokens when expecting 4" % len(list)

	# ok, value is 3rd list element
	eddieElvin.ELVINPORT = int(list[2])		# set the config option
	log.log( "<Config>ELVINPORT(), elvin port set to '%d'." % (eddieElvin.ELVINPORT), 6 )


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
		"DEF"		: definition.DEF,
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
		"ELVINHOST"	: ELVINHOST,
		"ELVINPORT"	: ELVINPORT,
           }

## Join all the above dictionaries to make the total keywords dictionary
keywords = {}
keywords.update(directives)
keywords.update(definitions)
keywords.update(settings)

##
## END - config.py
##
