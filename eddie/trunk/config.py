#!/opt/local/bin/python 
## 
## File		: config.py 
## 
## Author	: Rod Telford 
## 
## Date		: 971211 
## 
## Description	: Otto Software Config
##
## $Id$
##

import directive

##
## This is a list of known directives we accept in otto config/rules files
##
directives = {  "INCLUDE"	: directive.INCLUDE,		\
		"SCANPERIOD"	: directive.SCANPERIOD,		\
		"FS"		: directive.FS,			\
                "SP"		: directive.SP,			\
	  	"PID"		: directive.PID,		\
		"M"		: directive.M,			\
		"R"		: directive.R,			\
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
