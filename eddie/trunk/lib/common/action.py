#!/opt/local/bin/python 
## 
## File		: action.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971217 
## 
## Description	: 
##
## $Id$
##
##

import os
import string
import regex
import sys
import definition
import log
import utils

# Elvin test...
import eddieElvin

# Page test
import snpp

#### CONSTANTS ####

DEFAULTSUBJ='Message from Eddie'

#### DEFINE ALL THE ACTIONS AVAILABLE ####

class action:
    def __init__(self):
	pass

    # email()
    def email(self, user, msg):
	# Multiple email recipients are seperated by '|'.
	multUsers = string.split( user, '|' )

	for u in multUsers:
	    string.strip(u)			# strip white space

	# Create user recipient list delimited by ','
	users = string.join( multUsers, ',' )

	try:
	    MSG = self.getMessage(msg)
	    subj = MSG.subject
	    body = MSG.message
	except KeyError:
	    # Use msg string as the body
	    subj = "Eddie Alert"
	    body = msg

	# run thru parseVars() to substitute variables from varDict
	subj = parseVars( subj, self.varDict )
	body = parseVars( body, self.varDict )

	print "    ACTION: email - recip:"+users+", subj:'"+subj+"', body:'"+body+"'"
	#print " varDict is ",self.varDict

	tmp = os.popen('/usr/lib/sendmail -t', 'w')
	#tmp = open('sendmail.tmp', 'w')
	tmp.write( 'To: '+users+'\n' )
	tmp.write( 'From: "Eddie" <eddie@connect.com.au>\n' )
	tmp.write( 'Reply-To: systems@connect.com.au\n' )
	tmp.write( 'Subject: ['+log.hostname+'] '+subj+'\n' )
	tmp.write( '\n' )
	tmp.write( body+'\n' )
	tmp.write( '.\n' )
	tmp.close()

	if not log.log( "<action>email(), email sent to '%s', subject '%s', body '%s'" % (u,subj,body), 9 ):
	    log.log( "<action>email(%s, '%s')" % (u,subj) ,5 )
	
	#e = eddieElvin.eddieElvin()
	#e.sendmsg( subj )



    # system()
    def system(self, cmd):
	# cmd contains the cmd to execute
	# TODO: can we check this cmd for security problems ??

	# Substitute variables in string
	cmd = parseVars( cmd, self.varDict )

	if len(cmd) == 0:
	    log.log( "<action>system(), Error, no command given", 2)
	    return

	# Call system() to execute the command
	log.log( "<action>system(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action>system(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action>system(), cmd '%s', return value %d" % (cmd,retval), 5 )


    # restart()
    def restart(self, cmd):
	# cmd is cmd to be executed with: '/etc/init.d/cmd start'.
	# cmd should not contain any path information, hence if '/'s are found it
	# is not executed.

	# Substitute variables in string
	cmd = parseVars( cmd, self.varDict )

	# Security: if cmd contains any illegal characters, "/#;!$%&*|~`", then we abort.
	#if string.find( cmd, '/' ) != -1:
	if utils.charpresent( cmd, '/#;!$%&*|~`' ) != 0:
	    log.log( "<action>restart(), Alert, restart() arg contains illegal character and is not being executed, cmd is '%s'" % (cmd), 3 )
	    return

	if len(cmd) == 0:
	    log.log( "<action>restart(), Error, no command given", 2)
	    return
	
	# Build command
	cmd = '/etc/init.d/'+cmd+' start'

	# Call system() to execute the command
	log.log( "<action>restart(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action>restart(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action>restart(), cmd '%s', return value %d" % (cmd,retval), 5 )


    # nice()
    def nice(self, *arg):
	# Can be called with absolute or relative priority as follows:
	# nice( val ) - val is new absolute priority,
	# nice( �ncr, val ) - incr is incrementor which should be one of '-' or '+'
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
	    log.log( "<action>nice(), Error, %d arguments found, expecting 1 or 2" % (len(arg)), 2 )
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
		log.log( "<action>nice(), Error, val out of range, val is %d, range is %d-%d" % (val,nice_min,nice_max), 2 )
		return
	elif len(arg) == 2:
	    # Relative priority given, incr must be '-' or '+'
	    incr = arg[0]
	    val = string.atoi(arg[1])
	    if incr != '-' and incr != '+':
		log.log( "<action>nice(), Error, incremental is '%s', expecting '-' or '+'" % (incr), 2 )
		return


	# If %pid not defined, error.
	try:
	    pid = varDict['pid']
	except KeyError:
	    log.log( "<action>nice(), Error, %pid is not defined", 2 )

	# Build command
	if incr == '':
	    cmd = '/usr/bin/renice %d %s' % (val,pid)
	else:
	    cmd = '/usr/bin/renice -n %s%d %s' % (incr,val,pid)

	# Call renice()
	log.log( "<action>nice(), calling os.system() with cmd '%s'" % (cmd), 8 )
	retval = os.system( cmd )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action>nice(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

	log.log( "<action>nice(), cmd '%s', return value %d" % (cmd,retval), 5 )


    # eddielog()
    def eddielog(self, *arg):
	# if one argument supplied, this text is logged with a loglevel of 0
	# if two arguments, first is text to log, second is log level.

	if len(arg) < 0 or len(arg) > 2:
	    log.log( "<action>log(), Error, %d arguments found, expecting 1 or 2" % (len(arg)), 2 )
	    return

	logstr = arg[0]

	# if two arguments given, second arg is log level.  Otherwise assume 0.
	if len(arg) == 2:
	    loglevel = string.atoi(arg[1])

	    # If loglevel out of range, error.
	    if loglevel < log.loglevel_min or loglevel > log.loglevel_max:
		log.log( "<action>log(), Error, loglevel out of range, loglevel is %d, range is %d-%d" % (loglevel,log.loglevel_min,log.loglevel_max), 2 )
		return
	else:
	    loglevel = log.loglevel_min

	# Parse the text string to replace variables
	logstr = parseVars( logstr, self.varDict )

	# Log the text
	retval = log.log( logstr, loglevel )

	# Alert if return value == 0
	if retval == 0:
	    log.log( "<action>log(), Alert, return value for log.log( '%s', %d ) is %d" % (logstr,loglevel,retval), 3 )
	else:
	    log.log( "<action>eddielog(), text '%s', loglevel %d" % (logstr,loglevel), 5 )


    # elvin()
    def elvin(self, msg):
	if eddieElvin.UseElvin == 0:
	    log.log( "<action>elvin(), Elvin is not available - skipping.", 8 )
	    print "<action>elvin(), Elvin is not available - skipping."
	    return 0

	# send a message via Elvin message system
	elvinServer = 'koro'
	elvinPort = 5678

	print "ELVIN: elvinServer:",elvinServer
	print "ELVIN: elvinPort:",elvinPort

	if len(msg) == 0:
	    # msg must contain something
	    log.log( "<action>elvin(), Error, msg is empty", 2 )
	    return

	try:
	    MSG = self.getMessage(msg)
	    msg = MSG.message
	except KeyError:
	    # Use msg string as the message
	    pass

	# Substitute variables in string
	msg = parseVars( msg, self.varDict )

	try:
	    e = eddieElvin.elvinTicker( elvinServer, elvinPort )
	except eddieElvin.ElvinError:
	    log.log( "<action>elvin(), Error, eddieElvin(%s, %d) could not connect" % (elvinServer,elvinPort), 2 )
	    return

	retval = e.sendmsg( msg )

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action>elvin(), Alert, return value for e.sendmsg('%s') is %d" % (msg,retval), 3 )
	else:
	    log.log( "<action>elvin('%s')" % (msg), 5 )


    # elvinPage()
    def elvinPage(self, pager, msg):
	# send a message via Elvin message system to Pager
	elvinServer = 'chintoo'
	elvinPort = 5678

	if len(msg) == 0:
	    # msg must contain something
	    log.log( "<action>elvinPage(), Error, msg is empty", 2 )
	    return

	try:
	    MSG = self.getMessage(msg)
	    msg = MSG.message
	except KeyError:
	    # Use msg string as the message
	    pass

	# Substitute variables in string
	msg = parseVars( msg, self.varDict )

	try:
	    e = eddieElvin.elvinPage( elvinServer, elvinPort )
	except eddieElvin.ElvinError:
	    log.log( "<action>elvinPage(), Error, eddieElvin(%s, %d) could not connect" % (elvinServer,elvinPort), 2 )
	    return

	retval = e.sendmsg(pager, msg)

	# Alert if return value != 0
	if retval != 0:
	    log.log( "<action>elvinPage(), Alert, return value for e.sendmsg('%s') is %d" % (msg,retval), 3 )
	else:
	    log.log( "<action>elvinPage('%s')" % (msg), 5 )


    # page()
    def page(self, pager, msg):
	# send a page via SNPP
	pageServer = 'chintoo'

	if len(msg) == 0:
	    # msg must contain something
	    log.log( "<action>page(), Error, msg is empty", 2 )
	    return

	try:
	    MSG = self.getMessage(msg)
	    msg = MSG.message
	except KeyError:
	    # Use msg string as the message
	    pass

	# Substitute variables in string
	msg = parseVars( msg, self.varDict )

	p = snpp.level1(pageServer)
	p.pager(pager)
	p.message(msg)


	try:
	    p.send()
	except snpp.SNPPpageFail:
	    log.log( "<action>page(), Error, %s, returned %s" % (pageServer,snpp.SNPPpageFail), 2 )
	    return

	log.log( "<action>page('%s')" % (msg), 5 )

    #
    # Utilities for action functions
    #

    # Get a MSG object from the M-tree specified by self.msg and msg
    def getMessage(self, msg):
	print "//// MDict:",self.MDict
	msgtree = string.split( self.msg, '.' )
	M = self.MDict[msgtree[0]]
	print "///// M:",M
	for m in msgtree[1:]:
	    M = M[m]
	    print "///// M:",M

	# Get final MSG object
	MSG = M[msg]
	print "//// MSG:",MSG

	return MSG

##
## General utilities for actions
##

# Parse text string replacing occurences of %var with corresponding value from
# vDict['var'].  Return modified string.
# If substitutions were made, recursively called itself again to make any
# more substitutions.
def parseVars(text, vDict):
    slash = 0		# true if '\' found
    varcheck = 0	# true if '%' found - so look for variable name
    modtext = ''	# the modified text string
    subcount = 0	# count substitutions

    for c in text:
	if varcheck == 1:
	    # found '%' - if text following it (up to white-space or another '%')
	    # is a key in vDict, then replace '%var' with the value of vDict['var'].
	    # TODO: also search for %{var}

	    # build list of valid alphanumeric characters
	    alphanum = chrange('0','9') + chrange('a','z') + chrange('A','Z') + ['_']
	    if (c in alphanum):

		# must be part of variable name
		varname = varname + c
	    else:
		varcheck = 0
		# end of variable name found
		if varname == '':
		    # no variable name - just print '%'
		    modtext = modtext + '%' + c
		else:
		    try:
			varvalue = vDict[varname]
			# convert any type to a string!
			valuestr = "%s" % varvalue
			modtext = modtext + valuestr + c
			subcount = subcount + 1
		    except KeyError:
			# not a valid variable name - just print '%varname'
			modtext = modtext + '%' + varname + c
		    varname = ''
	elif (c == '%') and (not slash):
	    # found '%' - set flag to start reading variable name.
	    # Note: ignore '%' with '\' before it, ie: '\%'.
	    varcheck = 1
	    varname = ''
	elif c == '\\':	# ' [vim bug - remove this comment later]
	    # if '\' found set slash flag to true.
	    slash=1
	else:
	    # Create modified text string
	    modtext = modtext + c
	    slash = 0
    
    if varcheck == 1:
	# string ended while still reading varname
	    if varname == '':
		# no variable name - just print '%'
		modtext = modtext + '%' + c
	    else:
		try:
		    varvalue = vDict[varname]
		    modtext = modtext + varvalue
		    subcount = subcount + 1
		except KeyError:
		    # not a valid variable name - just print '%varname'
		    modtext = modtext + '%' + varname

    # Recurse if substitutions were made.
    if subcount > 0:
	modtext = parseVars(modtext, vDict)

    return modtext


def chrange(first,last):
    return map(chr,range(ord(first),ord(last)+1))


##
## END - action.py
##
