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
## This is a list of known directives we accept in an otto rules file
##
directives = {  "FS" : directive.FS,	\
                "SP" : directive.SP,	\
	  	"PID": directive.PID,	\
		"M"  : directive.M,	\
		"R"  : directive.R,	\
		"D"  : directive.D,	\
		"A"  : directive.A }

##
## Rules File
##
rules = 'config/fs.rules'


##
## END - config.py
##