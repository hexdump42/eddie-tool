## 
## File		: action.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 971217 
## 
## Description	: 
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2001
##
## The author accepts no responsibility for the use of this software and
## provides it on an ``as is'' basis without express or implied warranty.
##
## Redistribution and use in source and binary forms are permitted
## provided that this notice is preserved and due credit is given
## to the original author and the contributors.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
########################################################################

import os, string, sys, log, utils

# Elvin
import eddieElvin4, definition

# Page test
#import snpp


#### CONSTANTS ####

DEFAULTSUBJ='Message from Eddie'


#### Exceptions ####

GetMessageError = 'GetMessageError'


#### DEFINE ALL THE ACTIONS AVAILABLE ####

class action:
    def __init__(self):
	# define a default From: address for email action
	try:
	    self.EMAIL_FROM	# do nothing if already set by config
	except:
	    self.EMAIL_FROM = os.getenv("USER")
	    if self.EMAIL_FROM == None:
		self.EMAIL_FROM = 'root'

	# define a default Reply-To: address for email action
	try:
	    self.EMAIL_REPLYTO	# do nothing if already set by config
	except:
	    self.EMAIL_REPLYTO = ''


    def email(self, user, msg, msgbody=None):
	"""The standard email action.
	user should be a standard string containing a standard email address
	or list of email addresses separated by either a ',' or '|' or an
	ALIAS containing the same.

	msg should be either a standard string which will be used as the
	email subject (and also the email body if msgbody==None) or the
	name of a MSG object.

	msgbody should be a string containing the body of the email, assuming
	that msg is also the subject.
	"""

	# Replace any ALIASes if needed.
#	if user in self.aliasDict.keys():
#	    user = self.aliasDict[user]
#	if msg in self.aliasDict.keys():
#	    msg = self.aliasDict[msg]
#	if msgbody in self.aliasDict.keys():
#	    msgbody = self.aliasDict[msgbody]

	# Multiple email recipients are seperated by '|'.
	multUsers = string.split( user, '|' )

	for u in multUsers:
	    string.strip(u)			# strip white space

	# Create user recipient list delimited by ','
	users = string.join( multUsers, ',' )

#	try:
#	    MSG = self.getMessage(msg)
#	    subj = MSG.subject
#	    body = MSG.message
#	except (KeyError, GetMessageError):
#	    # Use msg string as the body
#	    #subj = "Eddie Alert"
#	    subj = msg
#	    if msgbody == None:
#		body = msg
#	    else:
#		body = msgbody

	if type(msg) != type("string"):
	    # if msg is not a string, assume it is a MSG object
	    body = msg.message
	    subj = msg.subject
	else:
	    # msg is a string
	    subj = msg
	    if msgbody == None:
		body = msg
	    else:
		body = msgbody

	# Create problem age and other statistics if this is not the first time
	# the problem was found.
	# Stored in %(problemage)s and %(problemfirstdetect)s
	self.varDict['problemage'] = ''
	self.varDict['problemfirstdetect'] = ''
	t = self.state.faildetecttime
	tl = self.state.lastfailtime
	if tl != t:
	    tage = self.state.age()
	    agestr = "Problem age: "
	    if tage[0] > 0:
		agestr = agestr + " %d year" % tage[0]
		if tage[0] > 1:
		    agestr = agestr + "s"
	    if tage[1] > 0:
		agestr = agestr + " %d month" % tage[1]
		if tage[1] > 1:
		    agestr = agestr + "s"
	    if tage[2] > 0:
		agestr = agestr + " %d day" % tage[2]
		if tage[2] > 1:
		    agestr = agestr + "s"
	    if tage[3] > 0:
		agestr = agestr + " %d hour" % tage[3]
		if tage[3] > 1:
		    agestr = agestr + "s"
	    if tage[4] > 0:
		agestr = agestr + " %d minute" % tage[4]
		if tage[4] > 1:
		    agestr = agestr + "s"
	    if tage[5] > 0:
		agestr = agestr + " %d second" % tage[5]
		if tage[5] > 1:
		    agestr = agestr + "s"
	    if agestr != "":
		self.varDict['problemage'] = agestr
	    self.varDict['problemfirstdetect'] = "First detected: %04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])


	# run thru parseVars() to substitute variables from varDict
	users = parseVars( users, self.varDict )
	subj = parseVars( subj, self.varDict )
	#subj = parseVars( subj, self.varDict )	# twice to substitute substituted variables!!
	body = parseVars( body, self.varDict )
	#body = parseVars( body, self.varDict )	# twice to substitute substituted variables!!

	#tmp = os.popen('/usr/lib/sendmail -t', 'w')
	tmp = utils.safe_popen('/usr/lib/sendmail -t', 'w')
	tmp.write( 'To: '+users+'\n' )
	tmp.write( 'From: %s\n' % (self.EMAIL_FROM) )
	tmp.write( 'Reply-To: %s\n' % (self.EMAIL_REPLYTO) )
	tmp.write( 'Subject: ['+log.hostname+'] '+subj+'\n' )
	tmp.write( 'X-Generated-By: %s:%s\n' % (os.uname()[1], sys.argv[0]) )
	tmp.write( '\n' )
	tmp.write( body+'\n' )
	#tmp.write( '.\n' )
	#tmp.close()
	utils.safe_pclose( tmp )

	if not log.log( "<action.py>action.email(), email sent to '%s', subject '%s', body '%s'" % (u,subj,body), 9 ):
	    log.log( "<action.py>action.email('%s', '%s', '%s')" % (u,subj,body[:20]) ,5 )
	


    # system()
    def system(self, cmd):
	# cmd contains the cmd to execute
	# TODO: can we check this cmd for security problems ??

	# Substitute variables in string
	cmd = parseVars( cmd, self.varDict )

	if len(cmd) == 0:
	    log.log( "<action.py>action.system(), Error, no command given", 2)
	    return

	# Call system() to execute the command
	log.log( "<action.py>action.system(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.system(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action.py>action.system(), cmd '%s', return value %d" % (cmd,retval), 5 )


    # restart()
    # returns: 0 = success
    #      1-255 = return code of restart call
    #       1001 = Security error - illegal characters in command
    #       1002 = Syntax error - command is empty
    def restart(self, cmd):
	# cmd is cmd to be executed with: '/etc/init.d/cmd start'.
	# cmd should not contain any path information, hence if '/'s are found it
	# is not executed.

	# Substitute variables in string
	cmd = parseVars( cmd, self.varDict )

	# Security: if cmd contains any illegal characters, "/#;!$%&*|~`", then we abort.
	#if string.find( cmd, '/' ) != -1:
	if utils.charpresent( cmd, '/#;!$%&*|~`' ) != 0:
	    log.log( "<action.py>action.restart(), Alert, restart() arg contains illegal character and is not being executed, cmd is '%s'" % (cmd), 3 )
	    return 1001

	if len(cmd) == 0:
	    log.log( "<action.py>action.restart(), Error, no command given", 2)
	    return 1002
	
	# Build command
	cmd = '/etc/init.d/'+cmd+' start'

	# Call system() to execute the command
	log.log( "<action.py>action.restart(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.restart(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action.py>action.restart(), cmd '%s', return value %d" % (cmd,retval), 5 )

	return retval


    # nice()
    def nice(self, *arg):
	# Can be called with absolute or relative priority as follows:
	# nice( val ) - val is new absolute priority,
	# nice( íncr, val ) - incr is incrementor which should be one of '-' or '+'
	# and val is relative offset.
	# %pid should contain the pid of the process who's priority is being
	# modified.
	# Note that Eddie must be running as Super-User to set a negative nice
	# level.

	# Min & max nice values.
	# TODO: Are these different for different systems?  Can we get max & mins
	# from system ??
	nice_min = -20
	nice_max = 19

	if len(arg) < 0 or len(arg) > 2:
	    log.log( "<action.py>action.nice(), Error, %d arguments found, expecting 1 or 2" % (len(arg)), 2 )
	    return

	# if one argument given, it is absolute priority level.
	# if two arguments given, first is incrementor ('-' or '+'), second is
	# offset
	if len(arg) == 1:
	    # Absolute priority given
	    val = string.atoi(arg[0])
	    incr = ''

	    # If val out of range, error.
	    if val < nice_min or val > nice_max:
		log.log( "<action.py>action.nice(), Error, val out of range, val is %d, range is %d-%d" % (val,nice_min,nice_max), 2 )
		return
	elif len(arg) == 2:
	    # Relative priority given, incr must be '-' or '+'
	    incr = arg[0]
	    val = string.atoi(arg[1])
	    if incr != '-' and incr != '+':
		log.log( "<action.py>action.nice(), Error, incremental is '%s', expecting '-' or '+'" % (incr), 2 )
		return


	# If %pid not defined, error.
	try:
	    pid = varDict['pid']
	except KeyError:
	    log.log( "<action.py>action.nice(), Error, %pid is not defined", 2 )

	# Build command
	if incr == '':
	    cmd = '/usr/bin/renice %d %s' % (val,pid)
	else:
	    cmd = '/usr/bin/renice -n %s%d %s' % (incr,val,pid)

	# Call renice()
	log.log( "<action.py>action.nice(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.nice(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action.py>action.nice(), cmd '%s', return value %d" % (cmd,retval), 5 )


    # eddielog()
    def eddielog(self, *arg):
	# if one argument supplied, this text is logged with a loglevel of 0
	# if two arguments, first is text to log, second is log level.

	if len(arg) < 0 or len(arg) > 2:
	    log.log( "<action.py>action.eddielog(), Error, %d arguments found, expecting 1 or 2" % (len(arg)), 2 )
	    return

	logstr = arg[0]

	# if two arguments given, second arg is log level.  Otherwise assume 0.
	if len(arg) == 2:
	    loglevel = string.atoi(arg[1])

	    # If loglevel out of range, error.
	    if loglevel < log.loglevel_min or loglevel > log.loglevel_max:
		log.log( "<action.py>action.eddielog(), Error, loglevel out of range, loglevel is %d, range is %d-%d" % (loglevel,log.loglevel_min,log.loglevel_max), 2 )
		return
	else:
	    loglevel = log.loglevel_min

	# Parse the text string to replace variables
	logstr = parseVars( logstr, self.varDict )

	# Log the text
	retval = log.log( logstr, loglevel )

	# Alert if return value == 0
	if retval == 0:
	    log.log( "<action.py>action.eddielog(), Alert, return value for log.log( '%s', %d ) is %d" % (logstr,loglevel,retval), 3 )
	else:
	    log.log( "<action.py>action.eddielog(), text '%s', loglevel %d" % (logstr,loglevel), 5 )


    # Send Elvin Ticker message
    def ticker(self, msg):
	if eddieElvin4.UseElvin == 0:
	    log.log( "<action.py>action.ticker(), Elvin is not available - skipping.", 7 )
	    return 0

	if type(msg) != type("string"):
	    # if msg is not a string, assume it is a MSG object
	    body = msg.subject
	else:
	    # msg is a string
	    body = msg

	if len(body) == 0:
	    # body must contain something
	    log.log( "<action.py>action.ticker(), Error, body is empty", 2 )
	    return

	# Substitute variables in string
	body = parseVars( body, self.varDict )

	try:
	    e = eddieElvin4.elvinTicker()
	except eddieElvin4.ElvinError:
	    log.log( "<action.py>action.ticker(), Error, elvinTicker() error", 2 )
	    return

	retval = e.sendmsg( body )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.ticker(), Alert, return value for e.sendmsg('%s') is %d" % (body,retval), 3 )
	else:
	    log.log( "<action.py>action.ticker('%s')" % (body), 5 )


    # elvinPage()
    def elvinPage(self, pager, msg):
	if eddieElvin.UseElvin == 0:
	    #log.log( "<action.py>action.elvin(), Elvin is not available - skipping.", 8 )
	    return 0

	# send a message via Elvin message system to Pager
	elvinServer = 'chintoo'
	elvinPort = 5678

	if type(msg) != type("string"):
	    # if msg is not a string, assume it is a MSG object
	    body = msg.subject
	else:
	    # msg is a string
	    body = msg

	if len(body) == 0:
	    # body must contain something
	    log.log( "<action.py>action.elvinPage(), Error, body is empty", 2 )
	    return

	# Substitute variables in string
	body = parseVars( body, self.varDict )

	try:
	    e = eddieElvin.elvinPage( elvinServer, elvinPort )
	except eddieElvin.ElvinError:
	    log.log( "<action.py>action.elvinPage(), Error, eddieElvin(%s, %d) could not connect" % (elvinServer,elvinPort), 2 )
	    return

	retval = e.sendmsg(pager, body)

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.elvinPage(), Alert, return value for e.sendmsg('%s') is %d" % (body,retval), 3 )
	else:
	    log.log( "<action.py>action.elvinPage('%s')" % (body), 5 )


    # Temporary: page via email for now...
    # page()
    def page(self, pager, msg):
	self.email(pager, msg)

    # Paging via SNPP to paging server
    # page()
    #def page(self, pager, msg):
#    def snpp_page(self, pager, msg):
#	# send a page via SNPP
#	pageServer = 'chintoo'
#
#	# Replace any ALIASes if needed.
#	if pager in self.aliasDict.keys():
#	    pager = self.aliasDict[pager]
#	if msg in self.aliasDict.keys():
#	    msg = self.aliasDict[msg]
#
#	if len(msg) == 0:
#	    # msg must contain something
#	    log.log( "<action.py>action.page(), Error, msg is empty", 2 )
#	    return
#
#	try:
#	    MSG = self.getMessage(msg)
#	    msg = MSG.message
#	except (KeyError, GetMessageError):
#	    # Use msg string as the message
#	    pass
#
#	# Substitute variables in string
#	msg = parseVars( msg, self.varDict )
#
#	p = snpp.level1(pageServer)
#	p.pager(pager)
#	p.message(msg)
#
#
#	try:
#	    p.send()
#	except snpp.SNPPpageFail:
#	    log.log( "<action.py>action.snpp_page(), Error, %s, returned %s" % (pageServer,snpp.SNPPpageFail), 2 )
#	    return
#
#	log.log( "<action.py>action.snpp_page('%s')" % (msg), 5 )


    def elvindb(self, table, data=None):
	"""Send information to remote database listener via Elvin.
	   Data to insert in db can be specified in the data argument as
	   'col1=data1, col2=data2, col3=data3' or if data is None it will
	   use self.storedict
	"""

	log.log( "<action.py>action.elvindb( table='%s' data='%s' )"%(table,data), 8 )

	if eddieElvin4.UseElvin == 0:
	    log.log( "<action.py>action.elvindb(), Elvin is not available - skipping.", 8 )
	    return 0

	try:
	    e = eddieElvin4.elvindb()
	except eddieElvin4.ElvinError:
	    log.log( "<action.py>action.elvindb(), Error, eddieElvin4.elvindb() could not connect", 2 )
	    return

	#print "created elvindb() connection to elvin"

	if data == None:
	    # if nothing passed in data storedict will be used
	    retval = e.send(table, self.storedict)
	else:
	    data = parseVars( data, self.varDict )	# substitute variables
	    datas = string.split(data, ',')		# separate key/val pairs
	    storedict = {}
	    for d in datas:
		(key,val) = string.split(d, '=')	# separate key & value
		key = string.strip(key)			# strip spaces

		val = utils.stripquote(val)		# strip spaces then quotes
		# try to convert val to float or int if possible
		try:
		    val = float(val)
		except ValueError:
		    try:
			val = int(val)
		    except ValueError:
			pass

		storedict[key] = val

	    #print "storedict:",storedict

	    retval = e.send(table, storedict)

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.elvindb('%s', dict), Alert, return value for e.send() is %d" % (table,retval), 3 )
	else:
	    log.log( "<action.py>action.elvindb('%s', dict): store ok" % (table), 7 )



    def elvinrrd(self, key, variable, data):
	"""Send information to remote RRDtool database listener via Elvin.
	"""

	log.log( "<action.py>action.elvinrrd( key='%s' variable='%s' data='%s' )"%(key,variable,data), 8 )

	if eddieElvin4.UseElvin == 0:
	    log.log( "<action.py>action.elvinrrd(), Elvin is not available - skipping.", 8 )
	    return 0

	try:
	    e = eddieElvin4.elvinrrd()
	except eddieElvin4.ElvinError:
	    log.log( "<action.py>action.elvinrrd(), Error, eddieElvin4.elvinrrd() could not connect", 2 )
	    return

	#print "created elvinrrd() connection to elvin"

	if variable == None or data == None:
	    # error
	    raise "elvinrrd exception, no variable or data defined"
	else:
	    key = parseVars( key, self.varDict )	# substitute variables
	    variable = parseVars( variable, self.varDict )	# substitute variables
	    data = parseVars( data, self.varDict )	# substitute variables

	    log.log( "<action.py>action.elvinrrd() sending: key='%s' variable='%s' data='%s'"%(key,variable,data), 8 )
	    retval = e.send(key, variable, data)

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action.py>action.elvinrrd(%s, %s, %s), Alert, return value for e.send() is %d" % (key,variable,data,retval), 3 )
	else:
	    log.log( "<action.py>action.elvinrrd(%s, %s, %s): store ok" % (key,variable,data), 7 )



##
## General utilities for actions
##

def parseVars(text, vDict):
    """Substitute variables in vDict dictionary into text string.  Use
    Python's builtin tricks for this.  Very simple!"""

    try:
	return text % vDict
    except KeyError:
	log.log( "<action>parseVars(), KeyError exception for '%s' from string '%s' with dictionary '%s'" % (sys.exc_value, text, vDict), 3 )
	return text
    except TypeError:
	log.log( "<action>parseVars(), TypeError exception for '%s' from string '%s' with dictionary '%s'" % (sys.exc_value, text, vDict), 3 )
	return text


##
## END - action.py
##
