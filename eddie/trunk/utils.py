#!/opt/local/bin/python 
## 
## File		: utils.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971217 
## 
## Description	: General utility functions
##
## $Id$
##
##

import regex
import string

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
    sre = regex.compile( "\([\t ]*[A-Za-z0-9_]*[\t ]*(\)\(.*\)\([\t ]*)[\t ]*\)" )
    for s in list:
	inx = sre.search( s )
	if inx != -1:
	    argline = sre.group(2)
	    arglist = string.split( argline, ',' )
	    newcmd = sre.group(1)		# build new command
	    i = 0				# count arguments so we don't put ',' before 1st argument
	    for a in arglist:
		a = string.strip( a )
		# if argument is not already enclosed in quotes ("" or '')
		if regex.search( "^[\"'].*[\"']$", a ) == -1:
		    a = '"' + a + '"'		# enclose it in quotes
		if i > 0:
		    newcmd = newcmd + ','	# put comma before argument 2-onwards
		newcmd = newcmd + a
		i = i + 1
	    newcmd = newcmd + sre.group(3)
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
## END - utils.py
##
