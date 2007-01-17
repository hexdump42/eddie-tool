
'''
File                : utils.py 

Start Date        : 19971217 

Description        : General utility functions

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 1997-2005'

__author__ = 'Chris Miles; Rod Telford'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''


## Python Modules
import re
import string
import threading
import os
import commands
import sys
import smtplib
## Eddie Modules
import log


## Exceptions
class WorkdirError(Exception):
    """An operation involved WORKDIR could not be completed.
    """



## Classes

class Stack:
    """General purpose stack object."""

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


## Functions

def trickySplit( line, delim ):
    """trickySplit( line, delim ) - split line by delimiter delim, but ignoring
       delimiters found inside ()'s, []'s, {}'s, '''s and ""'s.
      
       eg: trickySplit( "email(root,'hi there'),system('echo hi, mum')", ',' )
       would return: [ "email(root,'hi there')", "system('echo hi, mum')" ]
    """

    parenCnt = 0                # count of ()'s
    curlyCnt = 0                # count of {}'s
    squareCnt = 0                # count of []'s
    doubleqCnt = 0                # count of ""'s
    quoteCnt = 0                # count of '''s

    list = []                        # list of split strings
    current = ''                # the current split string

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


def quoteArgs( list ):
    """quoteArgs( list ) - cycle through list of strings, if the string looks like a
       function call (eg: "blah( a, b, c )") then put quotes around each of the
       arguments.  [Useful if you want to pass the string to eval()].  eg: the
       previous example would be converted to 'blah( "a", "b", "c" )'."""

    newlist = []
    sre = re.compile( "([\t ]*[A-Za-z0-9_]*[\t ]*\()(.*)([\t ]*\)[\t ]*)" )
    for s in list:
        inx = sre.search( s )
        if inx != None:
            argline = inx.group(2)
            arglist = string.split( argline, ',' )
            newcmd = inx.group(1)                # build new command
            i = 0                                # count arguments so we don't put ',' before 1st argument
            for a in arglist:
                a = string.strip( a )
                # if argument is not already enclosed in quotes ("" or '')
                if re.search( "^[\"'].*[\"']$", a ) == None:
                    a = '"' + a + '"'                # enclose it in quotes
                if i > 0:
                    newcmd = newcmd + ','        # put comma before argument 2-onwards
                newcmd = newcmd + a
                i = i + 1
            newcmd = newcmd + inx.group(3)
            newlist.append( newcmd )                # add our "quote-arg'd" command to list
        else:
            newlist.append( s )                        # add un-changed command to list
    
    return newlist
        
 

def charpresent( s, chars ):
    """charpresent( s, chars ) - returns 1 if ANY of the characters present in the string
       chars is found in the string s.  If none are found, 0 is returned."""

    for c in chars:
        if string.find( s, c ) != -1:
            return 1
    return 0


def stripquote( s ):
    """stripquote( s ) - strips start & end of string s of whitespace then
       strips " or ' from start & end of string if found - repeats stripping
       " and ' until none left."""

    # if not a string, don't touch it
    if type(s) != type("string"):
        return s

    # strip whitespace from ends
    s = string.strip( s )

    # strip quotes from ends (only in pairs)
    while len(s) > 0 and (s[0] in ["'", '"'] and s[-1] in ["'", '"']):
        if s[0] == "'" or s[0] == '"':
            s = s[1:]
        if s[-1] == "'" or s[-1] == '"':
            s = s[:-1]

    return s


def atom( ch ):
    """atom( ch ) - ascii-to-multiplyer - converts ascii char to a time multiplyer.
       eg: s=seconds, m=minutes, h=hours, d=days, w=weeks, c=calendar=months, y=years"""

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
        mult = 60*60*24*30                        # not exact...
    elif ch == 'y' or ch == 'Y':
        mult = 60*60*24*365
    else:
        mult = None

    return mult
        

def val2secs( value ):
    """
    Convert a time string to seconds.
    Return None if failed.
    """

    if re.search( '[mshdwcyMSHDWCY]', value ) == None:
        return string.atoi(value)
    timech = value[-1]
    value = value[:-1]
    mult = atom( timech )
    if mult == None:
        return None                # error parsing multiplier character
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


# Two facilities to send email are possible.  The default is
# to use the Python smtplib to directly connect to an SMTP
# server.  The second is to send mail via a sendmail binary.
#  sendmail_smtp = use smtplib
#  sendmail_bin  = use sendmail binary
SENDMAIL_FUNCTION = "sendmail_smtp"

# default sendmail binary location
# can be overriden from eddie.cf
SENDMAIL = '/usr/lib/sendmail'

# From: and Reply-To: headers will default to current user
# if not set in config.
EMAIL_FROM = None
EMAIL_REPLYTO = None

def sendmail( headers, body ):
    """Function to standardize email sending for EDDIE functions.
    Call the selected function to send email.

    Returns >=1 on success; 0 on failure.
    """

    exec "r = %s( headers, body )" % (SENDMAIL_FUNCTION)
    return r


def sendmail_bin( headers, body ):
    """Function to standardize email sending for EDDIE functions.

    Calls sendmail (from the SENDMAIL setting) passing it the headers
    and body strings.  headers should contain all the relevent headers
    (at least "To:" and usually "Subject:").

    Returns 1 on success; 0 on failure.
    """

    if not os.path.exists( SENDMAIL ):
        raise "utils.sendmail_bin exception", "sendmail not found, check SENDMAIL setting: '%s'"%(SENDMAIL)

    # make sure headers ends in carriage-return
    if headers[-1] != '\n':
        headers = headers + '\n'

    # add default headers if not already specified
    global EMAIL_FROM
    if not re.search( "^From:", headers, re.M ):
        if EMAIL_FROM == None:
            EMAIL_FROM = os.getenv("USER")
            if EMAIL_FROM == None:
                EMAIL_FROM = 'root'
        headers = headers + 'From: %s\n' % (EMAIL_FROM)

    if not re.search( "^Reply-To:", headers, re.M ):
        if EMAIL_REPLYTO != None:
            headers = headers + 'Reply-To: %s\n' % (EMAIL_REPLYTO)

    try:
        hostname = os.uname()[1]
    except AttributeError:
        import platform
        hostname = platform.node()
    headers = headers + 'X-Generated-By: %s:%s\n' % (hostname, sys.argv[0])

    # send the email via the sendmail binary
    tmp = safe_popen(SENDMAIL+' -t', 'w')
    tmp.write( headers )
    tmp.write( '\n' )
    tmp.write( body )
    safe_pclose( tmp )

    return 1


# Default SMTP servers for sendmail_smtp to use.  Overridden
# by SMTP_SERVERS option in config.
SMTP_SERVERS = ['localhost']

def sendmail_smtp( headers, body ):
    """Function to standardize email sending for EDDIE functions.

    Connects to a list of SMTP servers until it succeeds in sending the mail. 

    Returns 1 on success; 0 on failure.
    """

    # make sure headers ends in carriage-return
    if headers[-1] != '\n':
        headers = headers + '\n'

    # add default headers if not already specified
    global EMAIL_FROM
    if not re.search( "^From:", headers, re.M ):
        if EMAIL_FROM == None:
            EMAIL_FROM = os.getenv("USER")
            if EMAIL_FROM == None:
                EMAIL_FROM = 'root'
        headers = headers + 'From: %s\n' % (EMAIL_FROM)

    if not re.search( "^Reply-To:", headers, re.M ):
        if EMAIL_REPLYTO != None:
            headers = headers + 'Reply-To: %s\n' % (EMAIL_REPLYTO)

    m = re.search("^To: (.*)$",headers, re.M)
    toaddr = m.group(1)        
    if toaddr.find(','):
        toaddr = toaddr.split(',')

    try:
        hostname = os.uname()[1]
    except AttributeError:
        import platform
        hostname = platform.node()
    headers = headers + 'X-Generated-By: %s:%s\n' % (hostname, sys.argv[0])

    msg = "%s\r\n%s" % (headers, body)

    # Try and send to each server in turn until we succeed
    errmsg = []
    for server in SMTP_SERVERS:
        try:
            smtpserv = smtplib.SMTP(server)
            smtpserv.sendmail(EMAIL_FROM, toaddr, msg)
            smtpserv.quit()
        except:
            errmsg.append("<utils>sendmail_smtp: Tried via %s: %s" % (server, sys.exc_info()[0]))
            continue
        else:
            log.log("<utils>sendmail_smtp: Sent mail via %s" % server,6)
            return 1

    # Don't complain unless we can't send mail via any server
    log.log("<utils>sendmail_smtp: Could not send email to %s via any servers %s" % (`toaddr`, SMTP_SERVERS),4)
    for msg in errmsg:
        log.log(msg,4)
    return 0



# Should be set by WORKDIR paramter in eddie.cf.  By default is None which
#  will throw if get_work_dir() is called without setting WORKDIR in eddie.cf.
WORKDIR = None

def get_work_dir():
    """Return the temporary working directory as a string.  This is the
    directory location set by WORKDIR in eddie.cf.  If this is not defined
    then an exception will be raised.
    """

    if WORKDIR:
        return str(WORKDIR)        # make sure we return a string
    else:
        raise WorkdirError( "WORKDIR has not been defined" )



def set_sub_work_dir( subdir ):
    """Return the full path to a directory (subdir) beneath WORKDIR.
    subdir will be created if it doesn't exist.
    """

    workdir = get_work_dir()
    worksubdir = os.path.join( workdir, subdir )
    if not os.path.isdir( worksubdir ):
        try:
            os.makedirs( worksubdir, 0700 )        # create all dirs - access by user only
        except OSError, err:
            raise WorkdirError( "Cannot create WORKDIR subdirectory '%s', %s" % (worksubdir, err) )

    return worksubdir


def typeFromString( val ):
    """
    Is the string "val" an integer, float, or string?  Return appropriate variable
    of appropriate class.
    If none of those castings succeed, then return 'None'.
    """

    try:
        return int(val)         # try as an integer
    except:
        try:
            return float(val)   # try as a float
        except:
            try:
                return str(val)  # return a string (almost every object has a __str__ method)
            except:
                log.log( "<utils>typeFromString: unhandled cast", 4 )
                return None


def parseVars(text, vDict):
    """
    Substitute variables in vDict dictionary into text string.  Use
    Python's builtin tricks for this.  Very simple!
    Note that it parses the text from one to five times, meaning variables can
    contain variables, as in:
      d["x"] = "some string"
      d["y"] = "x is '%(x)s'"
      d["z"] = "y is '%(y)s'"
      parseVars("%(z)s", d) => "y is '%(y)s'" => "y is 'x is '%(x)s''" => "y is 'x is 'some string''"
    """

    # Keep parsing the text string until there are no '%(', or we've done a few parses...
    parses = 0
    while ( parses == 0 or text.find('%(') >= 0 ) and parses < 5:
        parses = parses + 1
        try:
            text = text % vDict
        except KeyError, msg:
            log.log( "<utils>parseVars(): KeyError exception for '%s' from string '%s' (%d) with dictionary '%s'" % (msg, text, parses, vDict), 5 )
            return text
        except TypeError, msg:
            log.log( "<utils>parseVars(): TypeError exception for '%s' from string '%s' (%d) with dictionary '%s'" % (msg, text, parses, vDict), 5 )
            return text

    return text


def create_child( doSTDs ):
    """
    Fork off a child process, and return its PID.
    Disassociate the child process from the parent process.

    Optionally close the STDIO file descriptors.
    """

    try:
        child_pid = os.fork()
        if child_pid:  # parent gets the child PID returned
            return child_pid
    except OSError, e:
        raise Exception, "create_child(): fork() failed: %s [%d]" % (e.strerror, e.errno)

    # create a new session for the child process (if available)
    if hasattr(os, 'setsid'):
        os.setsid()

    # fork() again so the parent (the session group leader), can exit.
    # We can now never gain a controlling terminal again.
#    if os.fork() != 0:
#        sys.exit(0)

    if doSTDs:
        # child closes its originating terminal connections:
        os.close(0)  # stdin
        os.close(1)  # stdout
        os.close(2)  # stderr
        nulld = '/dev/null'
        if (hasattr(os, 'devnull')):
            nulld = os.devnull
        # This call to open is guaranteed to return the lowest file descriptor,
        # which will be 0 (stdin), since it was closed above.
        sys.stdin  = open(nulld, 'r')
        sys.stdout = open(nulld, 'a+')
        sys.stderr = open(nulld, 'a+', 0)

    return 0  # child gets "0" returned


##
## END - utils.py
##
