#!/opt/local/bin/python 
## 
## File         : parseConfig.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Parses otto configuration files
##
## $Id$
##

import os
import string
import regex
import directive
import definition
import config

# Define exceptions
#ParseFailure = 'ParseFailure'

def readFile(file, ruleList, defDict, MDict):

    # Get the directory name of the base config file
    dir = file[:string.rfind(file, '/')]+'/'

    # List the known directives we accept from the config
    directives = config.directives
    
    conf = open(file, 'r')
    count = 0


    while 1:
	line = conf.readline()
	count = count + 1
	if not line: break

	line = string.rstrip(line)

	# **ROD** - why do you do stuff to 'wl' then use 'line' again below??
	wl = string.strip(line)
	if wl[:1] != '#' and len(wl) > 0:

	    # Strip any comments (#) from end of line
	    hashpos = regex.search( '#.*', line )
	    if hashpos != -1:
		line = line[:hashpos]
	    line = string.strip(line)

	    elements = string.split(line)

	    d = elements[0]
	    
	    if d == 'INCLUDE':
	    	# recursively read the INCLUDEd file
	    	readFile(dir+elements[1][1:-1], ruleList, defDict, MDict)
		continue

	    if directives.has_key(d):

		#
		# Check for special multiline directive M message
		#
		if d == 'M':
		    mess = line + '\n'

		    while 1:
			l = conf.readline()
			count = count + 1
			if l[:1] == '.': break
			mess = mess + l

		    action = directives[d](mess)

		else:
		    try:
			action = directives[d](line)
		    except (directive.ParseFailure, definition.ParseFailure):
			print "Parse failure in %s on line %d - skipping (line follows)\n%s" % (file, count, line)
			continue
		
		if action.basetype == 'Directive':
		    ruleList + action
		elif action.basetype == 'Definition':
		    if action.type == 'DEF':
			defDict[action.name] = action.text
		    elif action.type == 'M':
			MDict + action
		    else:
			print "Do wot with action : ",action," ??"
		elif action.basetype == 'ConfigOption':
		    # ummm... do nothing!
		    pass
		else:
		    print "Unknown type '"+action.basetype+"' for action: "+action

	    else:
	       print "Ignoring Unknown Directive %s on line %s of %s" % (d, count, file)

