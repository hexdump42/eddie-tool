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

##
## This is a list of known directives we accept in otto config/rules files
##

# TODO - SCANPERIOD should be sumthin like 'config.SCANPERIOD'

directives = {  "SCANPERIOD"	: directive.SCANPERIOD,		\
		"M"		: definition.M,			\
		"DEF"		: definition.DEF,		\
		"FS"		: directive.FS,			\
                "SP"		: directive.SP,			\
	  	"PID"		: directive.PID,		\
		"D"		: directive.D,			\
		"A"		: directive.A			}

##
## Rules File
##
rules = 'config/fs.rules'

##
## Scan Period in seconds (default is 10 minutes)
##
scanperiod = 10*60

##
## Parse rule-list and pull out Config commands.
##
def parseConfig( ruleList ):
    #directive.SCANPERIOD.setConfig( ruleList['SCANPERIOD'].value() )
    ruleList.delete( 'SCANPERIOD' )

##
## END - config.py
##
