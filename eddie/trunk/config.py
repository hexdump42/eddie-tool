#!/opt/local/bin/python 
## 
## File		: config.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971211 
## 
## Description	: Otto Software Config
##
## $Id$
##

import directive
import definition
import string
import regex
import log


## Define exceptions
ParseFailure = 'ParseFailure'

##
## Scan Period in seconds (default is 10 minutes)
##
scanperiod = 10*60

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


##
## CONFIGURATION OPTIONS
##

## SCANPERIOD - the time (in seconds) to pause between checks
class SCANPERIOD(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'SCANPERIOD[\t ]+\([a-zA-Z0-9]+\)[\t \n]*'
	value = self.parseRaw()
	value = self.val2secs( value )		# convert value to seconds
	global scanperiod 		# how do I access global scanperiod that already exists?
	scanperiod = value			# set the config option
	print "<SCANPERIOD> scanperiod set to %d seconds." % (scanperiod)

    def val2secs( self, value ):
	if regex.search( '[mshdwcyMSHDWCY]', value ) == -1:
	    return string.atoi(value)
	timech = value[-1]
	value = value[:-1]
	if timech == 's' or timech == 'S':
	    mult = 1
	elif timech == 'm' or timech == 'M':
	    mult = 60
	elif timech == 'h' or timech == 'H':
	    mult = 60*60
	elif timech == 'd' or timech == 'D':
	    mult = 60*60*24
	elif timech == 'w' or timech == 'W':
	    mult = 60*60*24*7
	elif timech == 'c' or timech == 'C':
	    mult = 60*60*24*30			# not exact...
	elif timech == 'y' or timech == 'Y':
	    mult = 60*60*24*365
	else:
	    print "Error in SCANPERIOD: timech is '%s'" % (timech)
	    mult = 0
	return string.atoi(value)*mult

## LOGFILE - where to store log messages
class LOGFILE(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'LOGFILE[\t ]+["\']\([a-zA-Z0-9/._=-]+\)["\'][\t \n]*'
	value = self.parseRaw()
	log.logfile = value			# set the config option
	print "<LOGFILE> logfile set to '%s'." % (log.logfile)


## LOGLEVEL - how much logging to do
class LOGLEVEL(ConfigOption):
    def __init__( self, *arg ):
	apply( ConfigOption.__init__, (self,) + arg )
	self.regexp = 'LOGLEVEL[\t ]+\([0-9]+\)[\t \n]*'
	value = self.parseRaw()
	log.loglevel = string.atoi(value)		# set the config option
	print "<LOGLEVEL> loglevel set to %d." % (log.loglevel)

##
## This is a list of known directives we accept in otto config/rules files
##

directives = {  "SCANPERIOD"	: SCANPERIOD,			\
		"LOGFILE"	: LOGFILE,			\
		"LOGLEVEL"	: LOGLEVEL,			\
		"M"		: definition.M,			\
		"DEF"		: definition.DEF,		\
		"A"		: definition.A,			\
		"FS"		: directive.FS,			\
                "SP"		: directive.SP,			\
	  	"PID"		: directive.PID,		\
		"D"		: directive.D,			}




##
## END - config.py
##
