#!/opt/local/bin/python 
## 
## File         : parseConfig.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Parses Eddie configuration files
##
## $Id$
##

import os
import string
import regex
import directive
import definition
import config
import log


def readFile(file, ruleList, defDict, MDict, ADict):

    # Get the directory name of the base config file
    dir = file[:string.rfind(file, '/')]+'/'

    # List the known directives we accept from the config
    directives = config.directives

    try:
    	conf = open(file, 'r')
    except IOError:
	print "Error opening file '%s'" % file;
	log.log( "<parseConfig>readFile(), Error, Cannot open '%s' - skipping" % (file), 2 )
	return

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

	    line = parseDefs(line, defDict)

	    line = string.strip(line)

	    elements = string.split(line)

	    d = elements[0]
	    
	    if d == 'INCLUDE':
	    	# recursively read the INCLUDEd file
		log.log( "<parseConfig>readFile(), reading INCLUDEd file %s" % elements[1], 8 )
		if string.find(elements[1], '/') > 0:
		    readFile(elements[1][1:-1], ruleList, defDict, MDict, ADict)
		else:
		    readFile(dir+elements[1][1:-1], ruleList, defDict, MDict, ADict)

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
			#print "<parseConfig>readFile(), created action '%s'" % (action.type)
		    except (directive.ParseFailure, definition.ParseFailure):
			log.log( "<parseConfig>readFile(), Alert, Parse failure in '%s' on line %d - skipping (line follows)\n%s" % (file, count, line), 3 )
			continue
		
		if action.basetype == 'Directive':
		    ruleList + action
		    log.log( "<parseConfig>readFile(), added action '%s' to ruleList" % (action.type), 9 )
		elif action.basetype == 'Definition':
		    if action.type == 'DEF':
			defDict[action.name] = action.text
		    elif action.type == 'M':
			MDict + action
		    elif action.type == 'A':
			ADict[action.name] = action.text
		    else:
			log.log( "<parseConfig>readFile(), Alert, unknown Definition type '%s' in '%s' on line %d" % (action,file,count), 3 )
		elif action.basetype == 'ConfigOption':
		    # ummm... do nothing!
		    pass
		else:
		    log.log( "<parseConfig>readFile(), Alert, unknown type '%s' for action '%s' in '%s' on line %d" % (action.basetype,action), 3 )

	    else:
	       log.log( "<parseConfig>readFile(), Alert, ignoring unknown directive '%s' in '%s' on line %d" % (d,file,count), 3 )
    conf.close()


# find any DEF's in line (ie: $SPAZ) and replace with definition
def parseDefs(line, defDict):
    defsrch = regex.compile( "\$\([A-Za-z0-9_]+\)" )

    pos = defsrch.search( line, 0 )
    while pos != -1 and pos < len(line):
	var = defsrch.group(0)[1:]		# get var name and strip '$'

	try:
	    replace = defDict[var]
	except KeyError:
	    replace = None
	
	if replace != None:
	    line = line[:pos] + replace + line[pos+len(var)+1:]

	pos = defsrch.search( line, pos+1 )

    return line

###
### END parseConfig.py
###
