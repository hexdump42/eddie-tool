#!/opt/local/bin/python 
## 
## File         : parseConfig.py 
## 
## Author       : Rod Telford 
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


def main():

    # List the known directives we accept from the config
    directives = {  "FS" : directive.FS,   \
		    "SP" : directive.SP,   \
		    "PID": directive.PID,  \
		    "M"  : directive.M,    \
		    "R"  : directive.R,    \
		    "D"  : directive.D,    \
		    "A"  : directive.A  }	

    file = 'config/fs.rules'
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
	    
		else:
		    action = directives[d](line)
	    else:
	       print "Ignoring Unknown Directive %s on line %s of %s" % (d, count, file)



if __name__ == "__main__":
    main()

