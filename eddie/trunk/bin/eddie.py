#!/opt/python152/bin/python
## 
## File         : eddie.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date         : 971204 
## 
## Description  : Eddie main program
##
## $Id$
##

EDDIE_VER='0.22'

# Standard Python modules
import sys, os, time, signal, re

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
                  os.path.join(basedir,'lib',osname,osver),
		  os.path.join(basedir,'lib',osname) ]


commonlibdir = os.path.join(basedir, 'lib/common')
sys.path = oslibdirs + [commonlibdir,] + sys.path
#print "sys.path:",sys.path

# Python common Eddie modules
import parseConfig, directive, definition, config, action, log, history

# Python OS-specific Eddie modules
import proc, df, netstat, system, iostat

# Main config file - this file INCLUDEs all other config files
configdir = os.path.join(basedir, 'config')
config_file = configdir + '/eddie.cf'

# Load Directive
config.loadExtraDirectives(os.path.join(commonlibdir, "Directives"))

# Exit Eddie cleanly
def eddieexit():
    # email admin any remaining messages
    log.sendadminlog(1)
    sys.exit()


# Signal Handler
def SigHandler( sig, frame ):

    if sig == signal.SIGHUP:
	# SIGHUP (Hangup) - reload config
	log.log( '<eddie>SigHandler(), SIGHUP encountered - reloading config', 3 )
	#
	# reset config and read in config and rules
	global Config
	Config = config.Config( '__main__' )

	# read in config and rules
	parseConfig.readConf(config_file, Config)

    elif sig == signal.SIGINT:
	# SIGINT (CTRL-c) - quit now
	log.log( '<eddie>SigHandler(), SIGINT (KeyboardInterrupt) encountered - quitting', 1 )
	print "\nEddie quitting ... bye bye"
	eddieexit()

    elif sig == signal.SIGTERM:
	# SIGTERM (Terminate) - quit now
	log.log( '<eddie>SigHandler(), SIGTERM (Terminate) encountered - quitting', 1 )
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


## Perform checks
def check(Config):
    # perform checks in current config group
    for d in Config.ruleList.keys():
	list = Config.ruleList[d]
	if list != None:
	    for i in list:
		log.log( "<eddie>check(), checking %s" % (i), 8 )
		i.docheck(Config)
	else:
	    log.log( "<eddie>check(), Config.ruleList['%s'] is empty" % (d), 4 )

    # perform checks for appropriate groups/hostnames
    for c in Config.groups:
	if c.name == log.hostname or (c.name in Config.classDict.keys() and log.hostname in Config.classDict[c.name]):
	    if Config.display == 0:
		log.log( "<eddie>check(), Calling check() with group %s" % (c.name), 5 )
	    else:
		log.log( "<eddie>check(), Calling check() with group %s" % (c.name), 8 )
	    check(c)
	else:
	    log.log( "<eddie>check(), Not checking group %s" % (c.name), 8 )

    # only display Config information once
    if Config.display == 0:
	Config.display = 1



# Parse command-line arguments
def doArgs(args, argflags):
    for a in args:
	if a == '-v' or a == '--version':
	    print "Eddie (c) Chris Miles and Rod Telford 1998"
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


# The guts of the Eddie program - sets up the lists, reads config info, gets
# system information, then performs the checking.
def eddieguts(Config, eddieHistory):

    # instantiate a process list
    log.log( "<eddie>eddieguts(), creating process object", 8 )
    directive.plist = proc.procList()

    # instantiate a disk usage list
    log.log( "<eddie>eddieguts(), creating df object", 8 )
    directive.dlist = df.dfList()

    # instantiate a netstat list
    log.log( "<eddie>eddieguts(), creating netstat object", 8 )
    directive.nlist = netstat.netstat()

    # instantiate a system object
    log.log( "<eddie>eddieguts(), creating system object", 8 )
    directive.system = system.system()

    # instantiate an iostat object
    log.log( "<eddie>eddieguts(), creating iostat object", 8 )
    directive.iostat = iostat.iostat()

    # Now do all the checking
    log.log( "<eddie>eddieguts(), beginning checks", 7 )
    check(Config)

    # Save history (debug.. FS only for now...)
    eddieHistory.save('FS',directive.dlist)



## Startup routine - setup then start main loop.
def main():
    # Catch most important signals
    signal.signal( signal.SIGALRM, SigHandler )
    signal.signal( signal.SIGHUP, SigHandler )
    signal.signal( signal.SIGINT, SigHandler )
    signal.signal( signal.SIGTERM, SigHandler )

    argflags = {}			# dict of argument flags

    # Parse command-line arguments
    doArgs(sys.argv[1:], argflags)	# parse arg-list (not program name)

    #    TODO: Is there a simpler Python-way of getting hostname ??
    tmp = os.popen('uname -n', 'r')
    hostname = tmp.readline()
    log.hostname = hostname[:-1]	# strip \n off end
    tmp.close()

    #print "[DEBUG] hostname:",log.hostname

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

    # Main Loop
    while 1:
	try:

	    # Count fds in use - for debugging
	    numfds = countFDs()
	    print "%d FDs in use." % (numfds)
	    log.log( "main(): FDs in use = %d." % (numfds), 7 )

	    # check if any config/rules files have been modified
	    # if so, re-read config
	    if Config.checkfiles():
		log.log( '<eddie>eddieguts(), config files modified - reloading config', 7 )
		#
		# reset config and read in config and rules
		global Config
		Config = config.Config( '__main__' )

		# read in config and rules
		parseConfig.readConf(config_file, Config)

	    # perform guts of Eddie
	    eddieguts(Config, history.eddieHistory)

	    # email admin the adminlog if required
	    log.sendadminlog()

	    # sleep for set period - only quits with CTRL-c
	    log.log( '<eddie>main(), sleeping for %d secs' % (config.scanperiod), 6 )
	    #print '<eddie>main(), sleeping for %d secs' % (config.scanperiod)

	    # Sleep by setting SIGALRM to go off in scanperiod seconds
	    #time.sleep( config.scanperiod )
	    signal.alarm( config.scanperiod )
	    signal.pause()

	except KeyboardInterrupt:
	    # CTRL-c hit - quit now
	    log.log( '<eddie>main(), KeyboardInterrupt encountered - quitting', 1 )
	    print "\nEddie quitting ... bye bye"
	    break



## Start...
if __name__ == "__main__":
    main()

    # email admin anything else...
    log.sendadminlog()

###
### END eddie.py
###
