#!/opt/local/bin/python 
## 
## File		: log.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 980107 
## 
## Description	: Eddie Software Logfile stuff
##
## $Id$
##

import time
import os

##
## Logfile & Log level (defaults)
##
logfile = "/var/log/eddie.log"
loglevel = 2

adminemail = 'root'
adminlevel = 0
adminlog = []
admin_notify = 86400	# default send admin summaries once per day
admin_notify_time = 0	# track time till next notify

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
	try:
	    logf = open( logfile, 'a' )
	    logf.write( logtext )
	    logf.close()
	    logged = logged + 1
	except IOError:
	    # Cannot open logfile for writing - save this problem in adminlog
	    print "<Log>log() - Fatal log error - cannot open logfile '%s'" % logfile
	    adminlog.append( "<Log>log() - Fatal log error - cannot open logfile '%s'" % logfile )

    if adminlevel > 0 and level <= adminlevel:
	# log to adminlog
	adminlog.append(logtext)
	logged = logged + 1

    return logged		# 0=not logged, >0=logged


# sendadminlog() - send adminlog list to adminemail only if there is something in
#   this list.
#   If override==1 then admin_notify times are ignored.
def sendadminlog( override=0 ):
    global admin_notify_time
    global adminlog

    if override == 0:
	# if no admin_notify_time set, set one and return
	if admin_notify_time == 0:
	    admin_notify_time = time.time() + admin_notify
	    return
    
	# if time hasn't reached admin_notify_time then return
	if time.time() < admin_notify_time:
	    return

    # time for notify - set new time and send the adminlog
    admin_notify_time = time.time() + admin_notify

    # if there isn't anything in adminlog don't bother
    if len(adminlog) == 0:
	return

    tmp = os.popen('/usr/lib/sendmail -t', 'w')
    tmp.write( 'To:'+adminemail+'\n' )
    tmp.write( 'From:eddie@connect.com.au\n' )
    tmp.write( 'Reply-To:systems@connect.com.au\n' )
    tmp.write( 'Subject: [%s] Eddie Admin Messages\n' % hostname )
    tmp.write( '\n' )
    tmp.write( "Greetings Eddie Admin '%s', the following log messages are\n" % adminemail )
    tmp.write( 'being delivered to you for your perusal.  Enjoy.\n\n' )
    tmp.write( "[Host:%s LogLevel=%d AdminLevel=%d AdminNotify=%s secs]\n" % (hostname,loglevel, adminlevel, admin_notify) )
    tmp.write( '------------------------------------------------------------------------------\n' )

    for i in adminlog:
	tmp.write( "%s" % (i) )

    tmp.write( '------------------------------------------------------------------------------\n' )
    tmp.close()

    # clear adminlog
    adminlog = []


##
## END - log.py
##
