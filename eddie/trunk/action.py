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

#### CONSTANTS ####

DEFAULTSUBJ='Message from Otto'


#### DEFINE ALL THE ACTIONS AVAILABLE ####

# email()
def email(user,*arg):
    # Multiple email recipients are seperated by '|'.
    multUsers = string.split( user, '|' )

    for u in multUsers:
	string.strip(u)			# strip white space
	# If there are 2 arguments (in arg), first arg is the Subject line,
	# 2nd arg is the Body text (can be a ref to an M definition, in
	# which case the given Subject line overrides the Subject defined
	# in the M).
	# If only 1 arg, it is either a reference to an M definition,
	# or a Body text string (a default Subject will be used).
	if len(arg) > 0:
	    subj = DEFAULTSUBJ

	    if len(arg) > 2:
		log.log( "<action>email(), Error, more than 2 arguments given '%s'" % arg, 2 )
		return

	    if len(arg) > 1:
		subj = arg[0]
		bodyarg = arg[1]
	    else:
		bodyarg = arg[0]

	    Mlist = definition.parseM( bodyarg, MDict )
	    if Mlist != ():
		subj = Mlist[0]
		body = Mlist[1]
	    else:
		body = bodyarg

	else:
	    # ERROR
	    log.log( "<action>email(), Error, no arguments given", 2 )

	subj = parseVars( subj, varDict )
	body = parseVars( body, varDict )
	body = parseVars( body, varDict )
	# body is run thru parseVars() twice to substitute variables that were
	# inserted into body from the first call to parseVars() ... bit silly
	# but it works...

	#print "    ACTION: email - recip:"+u+", subj:'"+subj+"', body:'"+body+"'"
	#print " varDict is ",varDict

	tmp = os.popen('/usr/lib/sendmail -t', 'w')
	#tmp = open('sendmail.tmp', 'w')
	tmp.write( 'To:'+u+'\n' )
	tmp.write( 'From:otto@connect.com.au\n' )
	tmp.write( 'Reply-To:systems@connect.com.au\n' )
	tmp.write( 'Subject: [TESTING] '+subj+'\n' )
	tmp.write( '\n' )
	tmp.write( body+'\n' )
	tmp.write( '.\n' )
	tmp.close()

	if not log.log( "<action>email(), email sent to '%s', subject '%s', body '%s'" % (u,subj,body), 9 ):
	    log.log( "<action>email(%s, '%s')" % (u,subj) ,5 )


# Parse text string replacing occurences of %var with corresponding value from
# vDict['var'].
def parseVars(text, vDict):
    slash = 0		# true if '\' found
    varcheck = 0	# true if '%' found - so look for variable name
    modtext = ''	# the modified text string
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
			modtext = modtext + varvalue + c
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
		except KeyError:
		    # not a valid variable name - just print '%varname'
		    modtext = modtext + '%' + varname

    return modtext

def chrange(first,last):
    return map(chr,range(ord(first),ord(last)+1))


# system()
def system(cmd):
    # cmd contains the cmd to execute
    # TODO: can we check this cmd for security problems ??

    # Substitute variables in string
    cmd = parseVars( cmd, varDict )

    if len(cmd) == 0:
        log.log( "<action>system(), Error, no command given", 2)
    	return

    # Can't use execvp() coz it replaces the Python process !!
    #fields = string.split( cmd )
    #if len(fields) == 0:
    #    log.log( "<action>system(), Error, no command given", 2)
    #	return
    #if len(fields) == 1:
    #	path = fields[0]
    #	args = ''
    #else:
    #	path = fields[0]
    #	args = fields[1:]
    #print "SYSTEM(): path='",path,"' args=",args
    #os.execvp( path, args )

    # Call system() to execute the command
    log.log( "<action>system(), calling os.system() with cmd '%s'" % (cmd), 8 )
    retval = os.system( cmd )

    # Alert if return value != 0
    if retval != 0:
	log.log( "<action>system(), Alert, return value for cmd '%s' is %d" % (cmd,retval), 3 )

    log.log( "<action>system(), cmd '%s', return value %d" % (cmd,retval), 5 )

# restart()
def restart(cmd):
    # cmd is cmd to be executed with: '/etc/init.d/cmd start'.
    # cmd should not contain any path information, hence if '/'s are found it
    # is not executed.

    # Security: if cmd contains any illegal characters, "/#;!$%&*|~`", then we abort.
    #if string.find( cmd, '/' ) != -1:
    if utils.charpresent( cmd, '/#;!$%&*|~`' ) != 0:
	log.log( "<action>restart(), Alert, restart() arg contains illegal character and is not being executed, cmd is '%s'" % (cmd), 3 )
	return

    # Substitute variables in string
    cmd = parseVars( cmd, varDict )

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


##
## END - action.py
##
