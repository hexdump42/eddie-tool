## 
## File		: utils.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 19971217 
## 
## Description	: General utility functions
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

import re, string, threading, os, commands, sys


##
## General purpose stack object
class Stack:
    def __init__(self):
	self.stack = []

    def __str__(self):
	return "%s" % self.stack

    def __len__(self):
	return len(self.stack)

    def __getitem__(self, item):
	return self.stack[item]

    def push(self, obj):
	self.stack.append( obj )

    def pop(self):
	obj = self.stack[-1]
	del self.stack[-1]
	return obj

    def top(self):
	if len(self.stack) == 0:
	    return None
	else:
	    return self.stack[-1]


##
## trickySplit( line, delim ) - split line by delimiter delim, but ignoring
## delimiters found inside ()'s, []'s, {}'s, '''s and ""'s.
##
## eg: trickySplit( "email(root,'hi there'),system('echo hi, mum')", ',' )
## would return: [ "email(root,'hi there')", "system('echo hi, mum')" ]
##
def trickySplit( line, delim ):
    parenCnt = 0		# count of ()'s
    curlyCnt = 0		# count of {}'s
    squareCnt = 0		# count of []'s
    doubleqCnt = 0		# count of ""'s
    quoteCnt = 0		# count of '''s

    list = []			# list of split strings
    current = ''		# the current split string

    for c in line:
	if c == '(':
	    parenCnt = parenCnt + 1
	elif c == ')':
	    parenCnt = parenCnt - 1
	elif c == '{':
	    curlyCnt = curlyCnt + 1
	elif c == '}':
	    curlyCnt = curlyCnt - 1
	elif c == '[':
	    squareCnt = squareCnt + 1
	elif c == ']':
	    squareCnt = squareCnt - 1
	elif c == '"':
	    doubleqCnt = 1 - doubleqCnt
	elif c == "'":
	    quoteCnt = 1 - quoteCnt
	elif c == delim:
	    if parenCnt == 0 and curlyCnt == 0 and squareCnt == 0 and doubleqCnt == 0 and quoteCnt == 0:
		# split here!
		list.append(current)
		current = ''
		continue

	current = current + c

    if len(current) > 0:
	list.append(current)

    return list


##
## quoteArgs( list ) - cycle through list of strings, if the string looks like a
##   function call (eg: "blah( a, b, c )") then put quotes around each of the
##   arguments.  [Useful if you want to pass the string to eval()].  eg: the
##   previous example would be converted to 'blah( "a", "b", "c" )'.
##
def quoteArgs( list ):
    newlist = []
    sre = re.compile( "([\t ]*[A-Za-z0-9_]*[\t ]*\()(.*)([\t ]*\)[\t ]*)" )
    for s in list:
	inx = sre.search( s )
	if inx != None:
	    argline = inx.group(2)
	    arglist = string.split( argline, ',' )
	    newcmd = inx.group(1)		# build new command
	    i = 0				# count arguments so we don't put ',' before 1st argument
	    for a in arglist:
		a = string.strip( a )
		# if argument is not already enclosed in quotes ("" or '')
		if re.search( "^[\"'].*[\"']$", a ) == None:
		    a = '"' + a + '"'		# enclose it in quotes
		if i > 0:
		    newcmd = newcmd + ','	# put comma before argument 2-onwards
		newcmd = newcmd + a
		i = i + 1
	    newcmd = newcmd + inx.group(3)
	    newlist.append( newcmd )		# add our "quote-arg'd" command to list
	else:
	    newlist.append( s )			# add un-changed command to list
    
    return newlist
	
 

##
## charpresent( s, chars ) - returns 1 if ANY of the characters present in the string
##   chars is found in the string s.  If none are found, 0 is returned.
##
def charpresent( s, chars ):
    for c in chars:
	if string.find( s, c ) != -1:
	    return 1
    return 0


##
## stripquote( s ) - strips start & end of string s of whitespace then
##   strips " or ' from start & end of string if found - repeats stripping
##   " and ' until none left.
##
def stripquote( s ):
    s = string.strip( s )

    while len(s) > 0 and (s[0] in ["'", '"'] and s[-1] in ["'", '"']):
	if s[0] == "'" or s[0] == '"':
	    s = s[1:]
	if s[-1] == "'" or s[-1] == '"':
	    s = s[:-1]

    return s


##
## atom( ch ) - ascii-to-multiplyer - converts ascii char to a time multiplyer.
##   eg: s=seconds, m=minutes, h=hours, d=days, w=weeks, c=calendar=months, y=years
##
def atom( ch ):
    if ch == 's' or ch == 'S':
	mult = 1
    elif ch == 'm' or ch == 'M':
	mult = 60
    elif ch == 'h' or ch == 'H':
	mult = 60*60
    elif ch == 'd' or ch == 'D':
	mult = 60*60*24
    elif ch == 'w' or ch == 'W':
	mult = 60*60*24*7
    elif ch == 'c' or ch == 'C':
	mult = 60*60*24*30			# not exact...
    elif ch == 'y' or ch == 'Y':
	mult = 60*60*24*365
    else:
	return 0

    return mult
	

def val2secs( value ):
    if re.search( '[mshdwcyMSHDWCY]', value ) == None:
	return string.atoi(value)
    timech = value[-1]
    value = value[:-1]
    mult = atom( timech )
    if mult == 0:
	return 0
    return string.atoi(value)*mult


# any thread performing a system call (i.e., os.system(),
# os.popen(), commands.getstatusoutput(), etc) must block on
# the systemcall_semaphore as only one thread appears to be able
# to do a system call at a time.
systemcall_semaphore = threading.Semaphore()

def safe_popen( cmd, mode ):
    """A thread-safe wrapper for os.popen() which did not appear to like
    being called simultaneously from multiple threads.  Obviously only
    allows one thread at a time to call os.popen().
    
    NOTE: safe_pclose() _must_ be called or the semaphore will never be
    released.
    """

    systemcall_semaphore.acquire()
    try:
	r = os.popen(cmd, mode)
    except:
	# if popen() raises an exception we must release the
	# semaphore lock before continuing, otherwise all further calls block -
	# which will lock up all the available threads...
	systemcall_semaphore.release()
	e = sys.exc_info()
	raise e[0], e[1]

    return r


def safe_pclose( fh ):
    """Close the file handler and release the semaphore."""

    try:
	fh.close()
    except:
	# if close() raises an exception we must release the
	# semaphore lock before continuing, otherwise all further calls block -
	# which will lock up all the available threads...
	systemcall_semaphore.release()
	e = sys.exc_info()
	raise e[0], e[1]

    systemcall_semaphore.release()


###safe_getstatusoutput_semaphore = threading.Semaphore()

def safe_getstatusoutput( cmd ):
    """A thread-safe wrapper for commands.getstatusoutput() which did not
    appear to like being called simultaneously from multiple threads.
    Semaphore locking allows only one call to commands.getstatusoutput()
    to be executed at any one time.

    NOTE: It is still not known whether a call to commands.getstatusoutput
    and popen() [and os.system() for that matter] can be called
    simultaneously.  If not, a global semaphore will have to be used to
    protect them all. UPDATE: This appears to be the case, so a global
    'systemcall' semaphore is now used.
    """

    systemcall_semaphore.acquire()
    try:
	(r, output) = commands.getstatusoutput( cmd )
    except:
	# if getstatusoutput() raises an exception we must release the
	# semaphore lock before continuing, otherwise all further calls block -
	# which will lock up all the available threads...
	systemcall_semaphore.release()
	e = sys.exc_info()
	raise e[0], e[1]

    systemcall_semaphore.release()

    return (r, output)

##
## END - utils.py
##
