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
import os

##
## Logfile & Log level (defaults)
##
logfile = "/var/log/otto.log"
loglevel = 2

adminemail = 'root'
adminlevel = 0
adminlog = []

loglevel_min = 0
loglevel_max = 9

# log() - if (level <= loglevel), text is appended to logfile
#         with date/time prepended (nothing is ever logged when
#         loglevel is 0).
#         If (level <= adminlevel) then store log in adminlog list (never store
#         anything if adminlevel is 0).
def log(text='', level=1):
    if loglevel == 0 and adminlevel == 0:
	return 0		# not logged

    datetime = time.asctime(time.localtime(time.time()))
    logtext = "%s [%d]:%s\n" % (datetime,level,text)

    logged = 0			# flag if anything is logged

    if level > 0 and level <= loglevel:
	# log to logfile
	logf = open( logfile, 'a' )
	logf.write( logtext )
	logf.close()
	logged = logged + 1
    
    if adminlevel > 0 and level <= adminlevel:
	# log to adminlog
	adminlog.append(logtext)
	logged = logged + 1

    return logged		# 0=not logged, >0=logged


# sendadminlog() - send adminlog list to adminemail only if there is something in
# this list.
def sendadminlog():
    tmp = os.popen('/usr/lib/sendmail -t', 'w')
    tmp.write( 'To:'+adminemail+'\n' )
    tmp.write( 'From:otto@connect.com.au\n' )
    tmp.write( 'Reply-To:systems@connect.com.au\n' )
    tmp.write( 'Subject: [TESTING] Otto Admin Messages\n' )
    tmp.write( '\n' )
    tmp.write( "Greetings Otto Admin '%s', the following log messages are\n" % adminemail )
    tmp.write( 'being delivered to you for your perusal.  Enjoy.\n' )
    tmp.write( "[LogLevel=%d AdminLevel=%d]\n" % (loglevel, adminlevel) )
    tmp.write( '------------------------------------------------------------------------------\n' )

    for i in adminlog:
	tmp.write( "%s\n" % (i) )

    tmp.write( '------------------------------------------------------------------------------\n' )
    tmp.close()


##
## END - log.py
##
