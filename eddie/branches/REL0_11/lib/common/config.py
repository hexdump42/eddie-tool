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

import string
import regex

import directive
import definition
import log
import proc
import utils


## Define exceptions
ParseFailure = 'ParseFailure'

##
## Scan Period in seconds (default is 10 minutes)
##
scanperiod = 10*60
scanperiodraw = '10m'

##
## The base configoption class.  Derive all config options from this base class.
##
class ConfigOption:
    def __init__(self, *arg):
	self.raw = arg[0]			# the raw line as read from config file
	self.basetype = 'ConfigOption'		# the object can know its own basetype
	self.type = string.split(self.raw)[0]	# the config option type of this instance
	self.regexp = ''			# the regexp to split the raw line into fields

    def parseRaw(self):
	sre = regex.compile( self.regexp )
	inx = sre.search( self.raw )
	if inx == -1:
	    # probably make an exception here.....
	    raise ParseFailure, "Error while parsing line: "+self.raw
	fieldlist = ()
	return sre.group(1)		# should only be 1 group


def val2secs( value ):
    if regex.search( '[mshdwcyMSHDWCY]', value ) == -1:
	return string.atoi(value)
    timech = value[-1]
    value = value[:-1]
    mult = utils.atom( timech )
    if mult == 0:
	log.log( "<Config>val2secs(%d,'%s'), Error : timech is '%s'" % (self,value,timech), 2 )
	return 0
    return string.atoi(value)*mult

##
## CONFIGURATION OPTIONS
##

## SCANPERIOD - the time (in seconds) to pause between checks
class SCANPERIOD(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'SCANPERIOD[\t ]+\([a-zA-Z0-9]+\)[\t \n]*'
	value = self.parseRaw()
	global scanperiodraw
	scanperiodraw = value			# keep the raw scanperiod
	value = val2secs( value )		# convert value to seconds
	if value > 0:
	    global scanperiod
	    scanperiod = value			# set the config option
	log.log( "<Config>SCANPERIOD(), scanperiod set to %s (%d seconds)." % (scanperiodraw, scanperiod), 6 )


## LOGFILE - where to store log messages
class LOGFILE(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'LOGFILE[\t ]+["\']\([a-zA-Z0-9/._=-]+\)["\'][\t \n]*'
	value = self.parseRaw()
	log.logfile = value			# set the config option
	log.log( "<Config>LOGFILE(), logfile set to '%s'." % (log.logfile), 6 )


## LOGLEVEL - how much logging to do
class LOGLEVEL(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'LOGLEVEL[\t ]+\([0-9]+\)[\t \n]*'
	value = self.parseRaw()
	log.loglevel = string.atoi(value)		# set the config option
	#log.log( "<Config>LOGLEVEL(), loglevel set to '%d'." % (log.loglevel), 6 )


## ADMIN - email address of Eddie administrator
# only currently supports 1 email address
# TODO: support more than 1 email address...
class ADMIN(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'ADMIN[\t ]+\([a-zA-Z0-9._@-]+\)[\t \n]*'
	value = self.parseRaw()
	log.adminemail = value
	log.log( "<Config>ADMIN(), admin set to '%s'." % (log.adminemail), 6 )


## ADMINLEVEL - how much logging to send to admin
class ADMINLEVEL(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'ADMINLEVEL[\t ]+\([0-9]+\)[\t \n]*'
	value = self.parseRaw()
	log.adminlevel = string.atoi(value)		# set the config option
	log.log( "<Config>ADMINLEVEL(), adminlevel set to '%d'." % (log.adminlevel), 6 )

## ADMIN_NOTIFY - how often to send admin-logs to admin
class ADMIN_NOTIFY(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'ADMIN_NOTIFY[\t ]+\([0-9]+[smhdwcy]?\)[\t \n]*'
	value = self.parseRaw()
	rawval = value
	value = val2secs( value )		# convert value to seconds
	if value > 0:
	    log.admin_notify = value		# set the config option
	log.log( "<Config>ADMIN_NOTIFY(), admin_notify set to %s (%d seconds)." % (rawval, log.admin_notify), 6 )

## INTERPRETERS - define the list of interpreters
class INTERPRETERS(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'INTERPRETERS[\t ]+\(.*\)[\t \n]*'
	value = self.parseRaw()
	proc.interpreters = string.split(value, ',')
	log.log( "<Config>INTERPRETERS(), interpreters defined as '%s'." % (proc.interpreters), 6 )

##
## This is a list of known directives we accept in Eddie config/rules files
##

directives = {  "SCANPERIOD"	: SCANPERIOD,
		"LOGFILE"	: LOGFILE,
		"LOGLEVEL"	: LOGLEVEL,
		"ADMIN"		: ADMIN,
		"ADMINLEVEL"	: ADMINLEVEL,
		"ADMIN_NOTIFY"	: ADMIN_NOTIFY,
		"INTERPRETERS"	: INTERPRETERS,
		"M"		: definition.M,
		"DEF"		: definition.DEF,
		"A"		: definition.A,
		"FS"		: directive.FS,
                "SP"		: directive.SP,
	  	"PID"		: directive.PID,
	  	"COM"		: directive.COM,
		"D"		: directive.D,
		"PORT"		: directive.PORT
}




##
## END - config.py
##
