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

#### CONSTANTS ####

DEFAULTSUBJ='Message from Otto'


#### DEFINE ALL THE ACTIONS AVAILABLE ####

# mail()
def mail(user,*arg):
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
		print "Error in mail() action: more than 2 arguments given:",arg
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
	    print "Error in mail() action: no arguments given."

	subj = parseVars( subj, varDict )
	body = parseVars( body, varDict )

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

	log.log( "mail sent to '"+u+"' subject '"+subj+"' body '"+body+"'" )


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
    pass
    print "    ACTION: system("+cmd+")"

# restart()
def restart(cmd):
    pass
    print "    ACTION: restart("+cmd+")"


##
## END - action.py
##
