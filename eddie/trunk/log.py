#!/opt/local/bin/python 
## 
## File		: log.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 980107 
## 
## Description	: Otto Software Logfile stuff
##
## $Id$
##

import time

##
## Logfile & Log level (defaults)
##
logfile = "/var/log/otto.log"
loglevel = 9


# log() - if level <= loglevel, text is appended to logfile
#         with date/time prepended (nothing is ever logged when
#         loglevel is 0).
def log(text='', level=1):
    if level > 0 and level <= loglevel:
	datetime = time.asctime(time.localtime(time.time()))
	logtext = "%s [%d]:%s\n" % (datetime,level,text)
	logf = open( logfile, 'a' )
	logf.write( logtext )
	logf.close()
	return 1		# logged
    else:
    	return 0		# not logged



##
## END - log.py
##
