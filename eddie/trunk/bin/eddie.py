#!/opt/python/bin/python
## 
## File         : eddie.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Eddie main program
##
## $Id$
##

EDDIE_VER='0.20'

# Standard Python modules
import sys, os, time, signal, thread

# Work out the base Eddie directory which should contain bin/, lib/, etc...
cwd = os.getcwd()
ewd = os.path.split(sys.argv[0])[0]
fullp = os.path.join(cwd, ewd)
basedir = os.path.join(fullp, '..')

# Determine OS type dynamically...
syscmd = os.popen( basedir + '/bin/systype', 'r' )
systype = syscmd.readline()[:-1]
syscmd.close()
if systype == '':
    os.stderr.write( 'Eddie: could not determine system type.\n' )

commonlibdir = os.path.join(basedir, 'lib/common')
oslibdir = os.path.join(basedir, 'lib/' + systype)

sys.path = [commonlibdir, oslibdir] + sys.path

# Python common Eddie modules
import parseConfig, directive, definition, config, action, log, history

# Python OS-specific Eddie modules
import proc, df, netstat

# Main config file - this file INCLUDEs all other config files
configdir = os.path.join(basedir, 'config')
config_file = configdir + '/eddie.cf'


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

    else:
	# un-handled signal - log & ignore it
	log.log( '<eddie>SigHandler(), unknown signal received, %d - ignoring' % sig, 3 )


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
	    log.log( "<eddie>check(), Calling check() with group %s" % (c.name), 8 )
	    print "[DEBUG] Calling check() with group %s" % (c.name)
	    check(c)
	else:
	    print "[DEBUG] Not checking group %s" % (c.name)



# Parse command-line arguments
def doArgs(args, argflags):
    for a in args:
	if a == '-v' or a == '--version':
	    print "Eddie (c) Chris Miles and Rod Telford 1998"
	    print "  cmiles@connect.com.au / rtelford@connect.com.au"
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
    log.log( "<eddie>eddieguts(), creating process list", 8 )
    directive.plist = proc.procList()

    # instantiate a disk usage list
    log.log( "<eddie>eddieguts(), creating df list", 8 )
    directive.dlist = df.dfList()

    # instantiate a netstat list
    log.log( "<eddie>eddieguts(), creating netstat list", 8 )
    directive.nlist = netstat.netstatList()

    # Now do all the checking
    log.log( "<eddie>eddieguts(), beginning checks", 7 )
    check(Config)

    # Save history (debug.. FS only for now...)
    eddieHistory.save('FS',directive.dlist)



## Startup routine - setup then start main loop.
def main():
    # Catch most important signals
    signal.signal( signal.SIGALRM, signal.SIG_IGN )
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

    print "[DEBUG] hostname:",log.hostname

    # instantiate global Config object
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
	    # perform guts of Eddie
	    eddieguts(Config, history.eddieHistory)

	    # email admin the adminlog if required
	    log.sendadminlog()

	    # sleep for set period - only quits with CTRL-c
	    log.log( '<eddie>main(), sleeping for %d secs' % (config.scanperiod), 6 )
	    print '<eddie>main(), sleeping for %d secs' % (config.scanperiod)

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
