#!/opt/local/bin/python
## 
## File         : otto.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Otto main program
##
## $Id$
##


import os
import time
import signal
import sys

import proc
import df
import parseConfig
import directive
import definition
import config
import action
import log
import history

# Main config file - this file INCLUDEs all other config files
config_file = 'config/otto.cf'


# Exit Otto cleanly
def ottoexit():
    # email admin any remaining messages
    log.sendadminlog()
    sys.exit()


# Signal Handler
def SigHandler( sig, frame ):
    global ourList		# global list of all directives
    global defDict		# global dictionary of DEFinitions
    global MDict		# global dictionary of Messages
    global ADict		# global dictionary of Actions

    if sig == signal.SIGHUP:
	# SIGHUP (Hangup) - reload config
	log.log( '<otto>SigHandler(), SIGHUP encountered - reloading config', 2 )
	#
	# reset lists and read in config and rules
	ourList = directive.Rules()
	defDict = {}
	MDict = definition.MsgDict()
	ADict = {}
	parseConfig.readFile(config_file, ourList, defDict, MDict, ADict)
	directive.ADict = ADict		# make ADict viewable in directive module
	action.MDict = MDict		# make MDict viewable in action module

    elif sig == signal.SIGINT:
	# SIGINT (CTRL-c) - quit now
	log.log( '<otto>SigHandler(), SIGINT (KeyboardInterrupt) encountered - quitting', 2 )
	print "\nOtto quitting ... bye bye"
	ottoexit()

    elif sig == signal.SIGTERM:
	# SIGTERM (Terminate) - quit now
	log.log( '<otto>SigHandler(), SIGTERM (Terminate) encountered - quitting', 2 )
	print "\nOtto quitting ... bye bye"
	ottoexit()

    else:
	# un-handled signal - log & ignore it
	log.log( '<otto>SigHandler(), unknown signal received, %d - ignoring' % sig, 2 )


# The guts of the Otto program - sets up the lists, reads config info, gets
# system information, then performs the checking.
def ottoguts(ottoHistory):

    #print "M: ",ourList['M']
    #print "D: ",ourList['D']
    #print "FS: ",ourList['FS']
    #print "PID: ",ourList['PID']
    #print "SP: ",ourList['SP']


    # instantiate a process list
    log.log( "<otto>ottoguts(), creating process list", 8 )
    directive.plist = proc.procList()

    # instantiate a disk usage list
    log.log( "<otto>ottoguts(), creating df list", 8 )
    directive.dlist = df.dfList()

    ## debugging ##
    #print "-- The following DEFs are defined: --"
    #for i in defDict.keys():
    #	print "%s=%s" % (i, defDict[i])
    #print "-- The following Ms are defined: --"
    #for i in MDict.keys():
    #	print "%s: Subject \"%s\"\n---BODY---\n%s\n----------" % (i, MDict.subj(i), MDict[i])
    #print "-- The following As are defined: --"
    #for i in ADict.keys():
    #	print "%s=%s" % (i, ADict[i])

    # Now do all the checking
    # note ... directive order is not defined (we don't currently care do we?)
    log.log( "<otto>ottoguts(), beginning checks", 8 )

    ## debugging - test with 'D' directive for now ##
    for d in ourList.keylist():
    #for d in ('COM',):
	list = ourList[d]
	if list != None:
	    for i in list:
		i.docheck()
	else:
	    log.log( "<otto>ottoguts(), ourList['%s'] is empty" % (d), 6 )

    # Save history (debug.. FS only for now...)
    ottoHistory.save('FS',directive.dlist)



def main():
    global ourList		# global list of all directives
    global defDict		# global dictionary of DEFinitions
    global MDict		# global dictionary of Messages
    global ADict		# global dictionary of Actions

    signal.signal( signal.SIGALRM, signal.SIG_IGN )
    signal.signal( signal.SIGHUP, SigHandler )
    signal.signal( signal.SIGINT, SigHandler )
    signal.signal( signal.SIGTERM, SigHandler )

    #    TODO: Is there a simpler Python-way of getting hostname ??
    #    TODO: Get the hostname at program startup, not here...
    tmp = os.popen('uname -n', 'r')
    hostname = tmp.readline()
    log.hostname = hostname[:-1]	# strip \n off end
    tmp.close()

    # New history object
    history.ottoHistory = history.history()

    # initialise our global lists/dicts
    ourList = directive.Rules()
    defDict = {}
    MDict = definition.MsgDict()
    ADict = {}

    # read in config and rules
    parseConfig.readFile(config_file, ourList, defDict, MDict, ADict)

    directive.ADict = ADict		# make ADict viewable in directive module
    action.MDict = MDict		# make MDict viewable in action module

    # Main Loop
    while 1:
	try:
	    # perform guts of Otto
	    ottoguts(history.ottoHistory)

	    # email admin the adminlog if required
	    log.sendadminlog()

	    # reset adminlog
	    log.adminlog = []

	    # sleep for set period - only quits with CTRL-c
	    log.log( '<otto>main(), sleeping for %d secs' % (config.scanperiod), 6 )
	    #print 'Press CTRL-C to quit'

	    # Sleep by setting SIGALRM to go off in scanperiod seconds
	    #time.sleep( config.scanperiod )
	    signal.alarm( config.scanperiod )
	    signal.pause()

	except KeyboardInterrupt:
	    # CTRL-c hit - quit now
	    log.log( '<otto>main(), KeyboardInterrupt encountered - quitting', 2 )
	    print "\nOtto quitting ... bye bye"
	    break



if __name__ == "__main__":
    main()

    # email admin anything else...
    log.sendadminlog()

###
### END otto.py
###
