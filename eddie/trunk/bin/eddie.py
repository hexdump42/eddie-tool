#!/opt/python152/bin/python
## 
## File         : eddie.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Start Date   : 971204 
## 
## Description  : Eddie main program
##
## $Id$
##

EDDIE_VER='0.24'


# Standard Python modules
import sys, os, time, signal, re, threading

print "Eddie v%s" % (EDDIE_VER)

# Work out the base Eddie directory which should contain bin/, lib/, etc...
cwd = os.getcwd()
ewd = os.path.split(sys.argv[0])[0]
fullp = os.path.join(cwd, ewd)
basedir = os.path.join(fullp, '..')

# Determine OS type dynamically...
try:
    # use old systype if available (backwards compatability)
    os.stat( basedir + '/bin/systype' )
    syscmd = os.popen( basedir + '/bin/systype', 'r' )
    systype = syscmd.readline()[:-1]
    syscmd.close()
    oslibdirs = [ os.path.join(basedir, 'lib/' + systype), ]
    print "systype:",systype
except os.error:
    systype = ''

if systype == '':
    # New system type determination (preferred)
    uname = os.uname()
    osname = uname[0]
    osver = uname[2]
    osarch = uname[4]
    print "systype: %s/%s/%s" % (osname,osver,osarch)
    oslibdirs = [ os.path.join(basedir,'lib',osname,osver,osarch),
                  os.path.join(basedir,'lib',osname,osarch,osver),
                  os.path.join(basedir,'lib',osname,osver),
                  os.path.join(basedir,'lib',osname,osarch),
		  os.path.join(basedir,'lib',osname) ]
    #print "oslibdirs:",oslibdirs


commonlibdir = os.path.join(basedir, 'lib/common')
sys.path = oslibdirs + [commonlibdir,] + sys.path
#print "sys.path:",sys.path

# Python common Eddie modules
import parseConfig, directive, definition, config, action, log, history, timeQueue

# Python OS-specific Eddie modules
import proc, df, netstat, system
try:
    import iostat
    module_iostat = 1
except:
    module_iostat = 0
    print "No iostat module."

# Main config file - this file INCLUDEs all other config files
configdir = os.path.join(basedir, 'config')
config_file = configdir + '/eddie.cf'

# Load Directive
config.loadExtraDirectives(os.path.join(commonlibdir, "Directives"))

# Exit Eddie cleanly
def eddieexit():
    log.log( '<eddie>eddieexit(), Eddie exiting cleanly.', 3 )
    # email admin any remaining messages
    log.sendadminlog(1)
    sys.exit()


def SigHandler( sig, frame ):
    """Handle all the signals we are interested in."""

    if sig == signal.SIGHUP:
	# SIGHUP (Hangup) - reload config
	log.log( '<eddie>SigHandler(), SIGHUP encountered - reloading config', 3 )

	# reset config and read in config and rules
	global Config
	Config = config.Config( '__main__' )

	# read in config and rules
	parseConfig.readConf(config_file, Config)

	# Initialise check queue
	q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
	buildCheckQueue(q, Config)
	Config.q = q

	#print "q:",q
	#print "q.qsize=%d" % (q.qsize())

	please_die.clear()
	global sthread
	sthread = threading.Thread(group=None, target=scheduler, name=None, args=(q,Config,please_die), kwargs={})
	sthread.start()	# start it up

    elif sig == signal.SIGINT:
	# SIGINT (CTRL-c) - quit now
	log.log( '<eddie>SigHandler(), SIGINT (KeyboardInterrupt) encountered - quitting', 1 )

	log.log( '<eddie>SigHandler(), signalling scheduler thread to die', 5 )
	please_die.set()
	sthread.join()

	print "\nEddie quitting ... bye bye"
	eddieexit()

    elif sig == signal.SIGTERM:
	# SIGTERM (Terminate) - quit now
	log.log( '<eddie>SigHandler(), SIGTERM (Terminate) encountered - quitting', 1 )

	log.log( '<eddie>SigHandler(), signalling scheduler thread to die', 5 )
	please_die.set()
	sthread.join()

	print "\nEddie quitting ... bye bye"
	eddieexit()

    elif sig == signal.SIGALRM:
	# SIGALRM (Alarm) - return to force a continue
	return

    else:
	# un-handled signal - log & ignore it
	log.log( '<eddie>SigHandler(), unknown signal received, %d - ignoring' % sig, 3 )


def countFDs():
    """Count number of file descriptors in use."""

    import errno
    fdcnt = 0
    for fd in range( 0, 1024 ):
	try:
	    stat = os.fstat( fd )
	    fdcnt = fdcnt + 1
	except os.error, ( errnum, str ):
	    if errnum != errno.EBADF:
		raise os.error, ( errnum, str )

    return fdcnt


def scheduler(q, Config, die_event):
    """The Eddie scheduler thread.  This thread tracks the queue of waiting
    checks and executes them in their own thread as required.  It attempts
    to limit the number of actual checking threads running to keep things
    sane."""

    while not die_event.isSet():

	while threading.activeCount() > config.num_threads:
	    # do nothing while we have no active threads to play with
	    # TODO: if we wait too long, something is probably wrong, so do something about it...
	    log.log( "<eddie>scheduler(), active thread count is %d - waiting till < %d" % (threading.activeCount(),config.num_threads), 8 )
	    try:
		time.sleep(1)
	    except IOError:
		# Indicates a signal received under Linux, just continue
		# coz main thread should be setting up to exit.
		log.log( "<eddie>scheduler(), IOError received by sleep(1) #1 - assume exiting so ignoring", 8 )
		pass

	# we have spare threads so get next checking object
	while not die_event.isSet():
	    (c,t) = q.head(block=1)	# wait for next object from queue
	    log.log( "<eddie>scheduler(), waiting object is %s at %s" % (c,t), 9 )
	    if t <= time.time():
		log.log( "<eddie>scheduler(), object %s,%s is ready to run" % (c,t), 9 )
		break
	    try:
		time.sleep(1)
	    except IOError:
		# Indicates a signal received under Linux, just continue
		# coz main thread should be setting up to exit.
		log.log( "<eddie>scheduler(), IOError received by sleep(1) #2 - assume exiting so ignoring", 8 )
		pass

	# break loop if we have been signalled to die
	if die_event.isSet():
	    break

	(c,t) = q.get(block=1)	# retrieve next object from queue

	if c.args.numchecks > 0:
	    # start check in a new thread
	    log.log( "<eddie>scheduler(), Starting new thread for %s, %s" % (c,t), 8 )
	    threading.Thread(group=None, target=c.docheck, name=None, args=(Config,), kwargs={}).start()
	else:
	    # when numchecks == 0 we don't do any checks at all...
	    log.log( "<eddie>scheduler(), Not scheduling checks for %s when numchecks=%d" % (c,c.args.numchecks), 7 )

    log.log( "<eddie>scheduler(), die_event received, scheduler exiting", 5 )



def buildCheckQueue(q, Config):
    """Build the queue of checks that the scheduler will start with."""

    for d in Config.ruleList.keys():
	list = Config.ruleList[d]
	if list != None:
	    for i in list:
		log.log( "<eddie>buildCheckQueue(), adding to Queue: %s" % (i), 8 )
		# if directive template is 'self', do not schedule it
		if i.args.template != 'self':
		    q.put( (i,0) )
	else:
	    log.log( "<eddie>buildCheckQueue(), Config.ruleList['%s'] is empty" % (d), 4 )

    for c in Config.groups:
	if c.name == log.hostname or (c.name in Config.classDict.keys() and log.hostname in Config.classDict[c.name]):
	    log.log( "<eddie>buildCheckQueue(), Adding checks from group %s to queue" % (c.name), 5 )
	    buildCheckQueue(q, c)
	else:
	    log.log( "<eddie>buildCheckQueue(), Not queueing group %s" % (c.name), 8 )


#def check(Config):
#    """Perform all the checks."""
#
#    # perform checks in current config group
#    for d in Config.ruleList.keys():
#	list = Config.ruleList[d]
#	if list != None:
#	    for i in list:
#		log.log( "<eddie>check(), checking %s" % (i), 8 )
#		i.docheck(Config)
#	else:
#	    log.log( "<eddie>check(), Config.ruleList['%s'] is empty" % (d), 4 )
#
#    # perform checks for appropriate groups/hostnames
#    for c in Config.groups:
#	if c.name == log.hostname or (c.name in Config.classDict.keys() and log.hostname in Config.classDict[c.name]):
#	    if Config.display == 0:
#		log.log( "<eddie>check(), Calling check() with group %s" % (c.name), 5 )
#	    else:
#		log.log( "<eddie>check(), Calling check() with group %s" % (c.name), 8 )
#	    check(c)
#	else:
#	    log.log( "<eddie>check(), Not checking group %s" % (c.name), 8 )
#
#    # only display Config information once
#    if Config.display == 0:
#	Config.display = 1



def doArgs(args, argflags):
    """Parse command-line arguments."""
    for a in args:
	if a == '-v' or a == '--version':
	    print "Eddie (c) Chris Miles and Rod Telford 1998-2000"
	    print "  cmiles@codefx.com.au / rtelford@codefx.com.au"
	    print "  Version: %s" % EDDIE_VER
	    eddieexit()
	elif a == '-h' or a == '--help' or a == '-?':
	    print "Eddie: help not yet available..."
	    eddieexit()
	elif a == '-sc' or a == '--showconfig':
	    argflags['showconfig'] = 1
	else:
	    print "Eddie: bad argument '%s'" % a
	    eddieexit()


def main():
    """Startup routine - setup then start main loop."""

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

    # New history object
    history.eddieHistory = history.history()

    # read in config and rules
    parseConfig.readConf(config_file, Config)

    if 'showconfig' in argflags.keys() and argflags['showconfig'] == 1:
	# Just display the configuration and exit
	print "---Displaying Eddie Configuration---"
	print Config
	eddieexit()

    # instantiate a process list
    log.log( "<eddie>eddieguts(), creating process object", 7 )
    directive.plist = proc.procList()

    # instantiate a disk usage list
    log.log( "<eddie>eddieguts(), creating df object", 7 )
    directive.dlist = df.dfList()

    # instantiate a netstat list
    log.log( "<eddie>eddieguts(), creating netstat object", 7 )
    directive.nlist = netstat.netstat()

    # instantiate a system object
    log.log( "<eddie>eddieguts(), creating system object", 7 )
    directive.system = system.system()

    if module_iostat:
        # instantiate an iostat object
        log.log( "<eddie>eddieguts(), creating iostat object", 7 )
        directive.iostat = iostat.iostat()


    # Main Loop
    # Initialise check queue
    q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
    buildCheckQueue(q, Config)
    Config.q = q

    #print "q:",q
    #print "q.qsize=%d" % (q.qsize())

    global please_die
    please_die = threading.Event()		# Event object to notify the scheduler to die
    global sthread
    sthread = threading.Thread(group=None, target=scheduler, name=None, args=(q,Config,please_die), kwargs={})
    sthread.start()	# start it up

    while 1:
	try:
	    ### Perform housecleaning duties

	    # Count fds in use - for debugging
	    numfds = countFDs()
	    log.log( "<eddie>main(), FDs in use = %d." % (numfds), 7 )

	    # check if any config/rules files have been modified
	    # if so, re-read config
	    if Config.checkfiles():
		log.log( '<eddie>main(), config files modified - signalling scheduler to die', 7 )
		please_die.set()
		sthread.join()

		log.log( '<eddie>main(), config files modified - reloading config', 7 )

		# reset config and read in config and rules
		global Config
		Config = config.Config( '__main__' )

		# read in config and rules
		parseConfig.readConf(config_file, Config)

		# Initialise check queue
		q = timeQueue.timeQueue(0)			# new timeQueue object, size is infinite
		buildCheckQueue(q, Config)
		Config.q = q

		#print "q:",q
		#print "q.qsize=%d" % (q.qsize())

		please_die.clear()

		global sthread
		sthread = threading.Thread(group=None, target=scheduler, name=None, args=(q,Config,please_die), kwargs={})
		sthread.start()	# start it up

	    # email admin the adminlog if required
	    log.sendadminlog()

	    time.sleep(10*60)	# sleep for 10 minutes between housekeeping duties

	except KeyboardInterrupt:
	    # CTRL-c hit - quit now
	    log.log( '<eddie>main(), KeyboardInterrupt encountered - quitting', 1 )
	    print "\nEddie quitting ... bye bye"
	    break


    # Save history (debug.. FS only for now...)
    #history.eddieHistory.save('FS',directive.dlist)

    # sleep for set period - only quits with CTRL-c
    #log.log( '<eddie>main(), sleeping for %d secs' % (config.scanperiod), 6 )

    # Sleep by setting SIGALRM to go off in scanperiod seconds
    #time.sleep( config.scanperiod )
    #signal.alarm( config.scanperiod )
    #signal.pause()



## Start...
if __name__ == "__main__":
    main()

    # email admin anything else...
    log.sendadminlog()

###
### END eddie.py
###
