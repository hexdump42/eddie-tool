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
import config

# Define exceptions
#ParseFailure = 'ParseFailure'

def readFile(file, ruleList):

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

	wl = string.strip(line)
	if wl[:1] != '#' and len(wl) > 0:
	    elements = string.split(line)

	    d = elements[0]
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
	    
		elif d == 'INCLUDE':
		    # recursively read the INCLUDEd file
		    readFile(dir+elements[1][1:-1], ruleList)
		    continue

		else:
		    try:
			action = directives[d](line)
		    except directive.ParseFailure, errr:
			print "Parse failure on line '"+line+"' - skipping."
			continue
		
		ruleList + action
	    else:
	       print "Ignoring Unknown Directive %s on line %s of %s" % (d, count, file)

