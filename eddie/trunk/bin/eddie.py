#! /usr/bin/env python
##
## File         : eddie.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Start Date   : 19971204 
## 
## Description  : EDDIE main program
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001-2004
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

__version__='0.33c'


# Python modules
import sys
import os
import time
import signal
import re
import threading


print "EDDIE v%s" % (__version__)

# Work out the base EDDIE directory which should contain bin/, lib/, etc...
cwd = os.getcwd()
ewd = os.path.split(sys.argv[0])[0]
fullp = os.path.join(cwd, ewd)
basedir = os.path.join(fullp, '..')
basedir = os.path.normpath(basedir)

# Determine system type
uname = os.uname()
osname = uname[0]
osver = uname[2]
osarch = uname[4]
systype = "%s/%s/%s" % (osname,osver,osarch)
print "systype:", systype

oslibdirs = [ os.path.join(basedir,'lib',osname,osver,osarch),
	      os.path.join(basedir,'lib',osname,osarch,osver),
	      os.path.join(basedir,'lib',osname,osver),
	      os.path.join(basedir,'lib',osname,osarch),
	      os.path.join(basedir,'lib',osname) ]

commonlibdir = os.path.join(basedir, 'lib/common')
# chris 2004-09-02: lib/common/Extra/ holds 3rd party modules
extralibdir = os.path.join(basedir, 'lib/common/Extra')
sys.path = oslibdirs + [commonlibdir,extralibdir] + sys.path

# EDDIE common modules
import parseConfig, directive, config, log, timeQueue, sockets, eddieElvin4, datacollect

# Main config file - this file INCLUDEs all other config files
configdir = os.path.join(basedir, 'config')
config_file = os.path.join(configdir, 'eddie.cf')

# Globals
global Config
global sthread
global cthread

# Read directive definitions from lib/common/Directives/
config.loadExtraDirectives(os.path.join(commonlibdir, "Directives"))


def start_threads(sargs, cargs):
    """Start any support threads that are required.
    Currently these are:
     - Scheduler thread: schedules directives to run [required]
     - Console Server thread: handles connections to console port [optional]
    """

    please_die.clear()		# reset thread signal

    global sthread		# the Scheduler thread
    sthread = threading.Thread(group=None, target=scheduler, name='Scheduler', args=sargs, kwargs={})
    sthread.start() 		# start the thread running

    global cthread		# the Console Server thread
    if config.consport > 0:	# don't start if CONSPORT=0
	cthread = threading.Thread(group=None, target=sockets.console_server_thread, name='Console', args=cargs, kwargs={})
	cthread.setDaemon(1)	# mark thread as Daemon-thread so EDDIE will not block when trying to terminate
	cthread.start()

    return()


def stop_threads():
    """
    Stop any threads started by start_threads().
    """

    please_die.set()		# signal threads to die

    sthread.join()		# wait for schedular thread to die

    if config.consport > 0:	# console thread not running if CONSPORT=0
	cthread.join()		# wait for console thread to die

    return()

 
def eddieexit():
    """
    Exit EDDIE cleanly.
    """

    log.log( '<eddie>eddieexit(): EDDIE exiting cleanly.', 5 )
    # email admin any remaining messages
    log.sendadminlog(1)
    sys.exit()


def SigHandler( sig, frame ):
    """
    Handle all the signals we are interested in.
    """

    if sig == signal.SIGHUP:
	# SIGHUP (Hangup) - reload config
	log.log( '<eddie>SigHandler(): SIGHUP encountered - reloading config', 5 )

        stop_threads()

	# reset config and read in config and rules
	global Config
	Config = config.Config( '__main__' )

	# read in config and rules
	parseConfig.readConf(config_file, Config)

	# Initialise check queue
	q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
	buildCheckQueue(q, Config)
	Config.q = q

        sargs = (q,Config,please_die)
        cargs = (Config, please_die, config.consport)

        start_threads(sargs, cargs)

    elif sig == signal.SIGINT:
	# SIGINT (CTRL-c) - quit now
	log.log( '<eddie>SigHandler(): SIGINT (KeyboardInterrupt) encountered - quitting', 1 )

	log.log( '<eddie>SigHandler(): signalling scheduler thread to die', 6 )
        stop_threads()

	try:
	    print "\nEDDIE quitting ... bye bye"
	except IOError:
	    pass	# if tty has gone it will cause this exception
	eddieexit()

    elif sig == signal.SIGTERM:
	# SIGTERM (Terminate) - quit now
	log.log( '<eddie>SigHandler(): SIGTERM (Terminate) encountered - quitting', 1 )

	log.log( '<eddie>SigHandler(): signalling scheduler thread to die', 6 )
        stop_threads()

	try:
	    print "\nEDDIE quitting ... bye bye"
	except IOError:
	    pass	# if tty has gone it will cause this exception
	eddieexit()

    elif sig == signal.SIGALRM:
	# SIGALRM (Alarm) - return to force a continue
	return

    else:
	# un-handled signal - log & ignore it
	log.log( '<eddie>SigHandler(): unknown signal received, %d - ignoring' % sig, 5 )


def countFDs():
    """Count number of file descriptors in use.
    """

    import errno
    fdcnt = 0
    for fd in range( 0, 1024 ):
	try:
	    stat = os.fstat( fd )
	    fdcnt = fdcnt + 1
	except os.error, ( errnum, str ):
	    if errnum != errno.EBADF:
		#raise os.error, ( errnum, str )
		log.log( '<eddie>countFDs(): exception os.error, %s, %s' %(errnum,str), 5 )

    return fdcnt


def scheduler(q, Config, die_event):
    """The EDDIE scheduler thread.  This thread tracks the queue of waiting
    checks and executes them in their own thread as required.  It attempts
    to limit the number of actual checking threads running to keep things
    sane.
    """

    while not die_event.isSet():

	loop_start = time.time()	# get time when loop started
	while threading.activeCount() > config.num_threads:
	    # do nothing while we have no active threads to play with
	    # TODO: if we wait too long, something is probably wrong, so do something about it...
	    log.log( "<eddie>scheduler(): active thread count is %d - waiting till < %d" % (threading.activeCount(),config.num_threads), 8 )
	    if time.time() - loop_start > 30*60:
		# if this loop has been running for over 30 mins, then all
		# threads are locked badly and something is wrong.  Force an
		# exit...
		# (there is no ability to kill threads in current Python implementation)
		log.log( "<eddie>scheduler(): active thread count has been %d for over %d mins - forcing exit" % (threading.activeCount(),time.time() - loop_start), 1 )
		eddieexit()

	    try:
		time.sleep(1)
	    except IOError:
		# Indicates a signal received under Linux, just continue
		# coz main thread should be setting up to exit.
		log.log( "<eddie>scheduler(): IOError received by sleep(1) #1 - assume exiting so ignoring", 8 )
		pass

	# we have spare threads so get next checking object
	while not die_event.isSet():
	    (c,t) = q.head(block=1)	# wait for next object from queue
	    log.log( "<eddie>scheduler(): waiting object is %s at %s" % (c,t), 9 )
	    if t <= time.time():
		log.log( "<eddie>scheduler(): object %s,%s is ready to run" % (c,t), 9 )
		break
	    try:
		time.sleep(1)
	    except IOError:
		# Indicates a signal received under Linux, just continue
		# coz main thread should be setting up to exit.
		log.log( "<eddie>scheduler(): IOError received by sleep(1) #2 - assume exiting so ignoring", 8 )
		pass

	# break loop if we have been signalled to die
	if die_event.isSet():
	    break

	(c,t) = q.get(block=1)	# retrieve next object from queue

	if c.args.numchecks > 0:
	    # start check in a new thread
	    thr = threading.Thread(group=None, target=c.safeCheck, name="%s"%(c), args=(Config,), kwargs={})
	    log.log( "<eddie>scheduler(): Starting new thread for %s, %s" % (c,thr), 8 )
	    thr.setDaemon(1)	# mark thread as Daemon-thread so EDDIE will not block when trying to terminate
	    			# with still-running threads.
	    thr.start()		# new thread starts running
	else:
	    # when numchecks == 0 we don't do any checks at all...
	    log.log( "<eddie>scheduler(): Not scheduling checks for %s when numchecks=%d" % (c,c.args.numchecks), 7 )

    log.log( "<eddie>scheduler(): die_event received, scheduler exiting", 8 )


def buildCheckQueue(q, Config):
    """
    Build the queue of checks that the scheduler will start with.
    """

    log.log( "<eddie>buildCheckQueue(): Adding directives to Queue for hostname '%s'" % (log.hostname), 8 )

    for i in Config.groupDirectives.keys():
	# if directive template is 'self', do not schedule it
	d = Config.groupDirectives[i]
	if d.args.template != 'self':
	    # chris 2002-12-24: skip directives specifying this hostname in excludehosts parameter
	    if log.hostname in d.excludehosts:
		log.log( "<eddie>buildCheckQueue(): skipped by excludehosts: %s" % (d), 8 )
	    else:
		log.log( "<eddie>buildCheckQueue(): adding to Queue: %s" % (d), 8 )
		q.put( (d,0) )

    for c in Config.groups:
	if c.name == log.hostname or (c.name in Config.classDict.keys() and log.hostname in Config.classDict[c.name]):
	    log.log( "<eddie>buildCheckQueue(): Adding checks from group %s to queue" % (c.name), 7 )
	    buildCheckQueue(q, c)
	else:
	    log.log( "<eddie>buildCheckQueue(): Not queueing group %s" % (c.name), 8 )


def doArgs(args, argflags):
    """
    Parse command-line arguments.
    """

    for a in args:
	if a == '-v' or a == '--version':
	    print "EDDIE (c) Chris Miles and Rod Telford 1998-2002"
	    print "  chris@psychofx.com / rtelford@psychofx.com"
	    print "  Version: %s" % __version__
	    eddieexit()
	elif a == '-h' or a == '--help' or a == '-?':
	    print "EDDIE: help not yet available..."
	    eddieexit()
	elif a == '-sc' or a == '--showconfig':
	    argflags['showconfig'] = 1
	else:
	    print "EDDIE: bad argument '%s'" % a
	    eddieexit()


def main():
    """
    Startup routine - setup then start main loop.
    """

    log.version = __version__	# Make version string available to other modules

    # Catch most important signals
    signal.signal( signal.SIGALRM, SigHandler )
    signal.signal( signal.SIGHUP, SigHandler )
    signal.signal( signal.SIGINT, SigHandler )
    signal.signal( signal.SIGTERM, SigHandler )

    argflags = {}			# dict of argument flags

    # Parse command-line arguments
    doArgs(sys.argv[1:], argflags)	# parse arg-list (not program name)

    # Get local hostname
    log.hostname = os.uname()[1]

    # instantiate global Config object
    global Config
    Config = config.Config( '__main__' )

    # data_modules handles access to all data collector modules
    data_modules = datacollect.DataModules()
    directive.data_modules = data_modules

    # read in config and rules
    parseConfig.readConf(config_file, Config)

    # don't log till now because log file location is defined in configuration
    log.log( "<eddie>main(): Configuration complete from '%s'" % (config_file), 6 )
    log.log( "<eddie>main(): EDDIE %s, systype: %s" % (__version__, systype), 5 )
    log.log( "<eddie>main(): oslibdirs: %s" % (oslibdirs), 8 )

    if 'showconfig' in argflags.keys() and argflags['showconfig'] == 1:
	# Just display the configuration and exit
	print "---Displaying EDDIE Configuration---"
	print Config
	eddieexit()

    # Initialise Elvin connections and thread to handle Elvin messaging
    try:
	elvin = eddieElvin4.Elvin()
    except eddieElvin4.ElvinInitError, details:
	log.log( "<eddie>main(): Elvin init failed, %s, Elvin functionality will be disabled."%(details), 5 )
	elvin = None
    else:
	elvin.startup()		# Start up the Elvin management thread
    Config.set_elvin(elvin)

    # Main Loop
    # Initialise check queue
    q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
    buildCheckQueue(q, Config)
    Config.q = q

    global please_die
    please_die = threading.Event()		# Event object to notify the scheduler to die
    global sthread

    sargs = (q,Config,please_die)
    cargs = (Config, please_die, config.consport)
    start_threads(sargs,cargs)

    while not please_die.isSet():
	try:
	    ### Perform housecleaning duties

	    # Count fds in use - for debugging
	    numfds = countFDs()
	    log.log( "<eddie>main(): FDs in use = %d." % (numfds), 8 )
	    log.log( "<eddie>main(): Threads in use = %d." % (threading.activeCount()), 8 )
	    log.log( "<eddie>main(): Threads: %s" % (threading.enumerate()), 8 )

	    # check if any config/rules files have been modified
	    # if so, re-read config
	    if Config.checkfiles():
		log.log( '<eddie>main(): config files modified - signalling scheduler to die', 7 )
                stop_threads()

		log.log( '<eddie>main(): config files modified - reloading config', 5 )

		# reset config and read in config and rules
		Config = config.Config( '__main__' )

		# read in config and rules
		parseConfig.readConf(config_file, Config)

		# Initialise check queue
		q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
		buildCheckQueue(q, Config)
		Config.q = q

                sargs = (q,Config,please_die)
                cargs = (Config, please_die, config.consport)
                start_threads(sargs,cargs)


	    # email admin the adminlog if required
	    log.sendadminlog()

	    #time.sleep(10*60)	# sleep for 10 minutes between housekeeping duties
	    please_die.wait(1*60)	# sleep for 1 minute between housekeeping duties
					# or until all threads signalled to exit

	except KeyboardInterrupt:
	    # CTRL-c hit - quit now
	    log.log( '<eddie>main(): KeyboardInterrupt encountered - quitting', 1 )
	    try:
		print "\nEDDIE quitting ... bye bye"
	    except IOError:
		pass	# if tty has gone it will cause this exception
	    eddieexit()


    log.log( '<eddie>main(): main thread signalled to die - exiting', 1 )
    eddieexit()




## Start...
if __name__ == "__main__":
    try:
	main()
    except:		# catch any uncaught exceptions so we can log them
	e = sys.exc_info()
	import exceptions
	if e[0] != exceptions.SystemExit:
	    import traceback
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    import string
	    tbstr = string.join(tb, '')
	    log.log( "<eddie.py>: EDDIE died with exception: %s, %s\n%s" % (e[0], e[1], tbstr), 1 )
	    log.sendadminlog()
	    print tbstr
	    print e[0], e[1]
	    sys.exit(1)


    # email admin anything else...
    log.sendadminlog()


###
### END eddie.py
###
