# encoding: utf-8

'''
File         : commands.py 

Start Date   : 20080513

Description  : Eddie-Tool command-line entry points.

$Id$
'''

__copyright__ = 'Copyright (c) Chris Miles 2008'

__author__ = 'Chris Miles'

__url__ = 'http://eddie-tool.psychofx.com/'

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

from version import version as __version__

# Python modules
import sys
import os
import time
import signal
import re
import threading
# optparse is only available in 2.3+, but optik provides the same 
# functionality for python 2.2
try:
    import optparse
except ImportError:
    try:
        import optik as optparse
    except ImportError:
        sys.stderr.write("Error: EDDIE requires Optik on Python 2.2.x (http://optik.sf.net)\n")
        sys.exit(1)


# Work out the base EDDIE directory which should contain bin/, lib/, etc...
# cwd = os.getcwd()
# ewd = os.path.split(sys.argv[0])[0]
# fullp = os.path.join(cwd, ewd)
# basedir = os.path.join(fullp, '..')
# basedir = os.path.normpath(basedir)

# Determine system type
try:
    import platform
except ImportError:
    try:
        uname = os.uname()
    except AttributeError,err:
        raise Exception( "Cannot determine platform: %s" %(err) )
    else:
        osname = uname[0]
        osver = uname[2]
        osarch = uname[4]
else:
    osname = platform.uname()[0]
    osver = platform.uname()[2]
    osarch = ''

systype = "%s/%s/%s" % (osname,osver,osarch)
#print "systype:", systype
 
    
# oslibdirs = [ os.path.join(basedir,'lib',osname,osver,osarch),
#               os.path.join(basedir,'lib',osname,osarch,osver),
#               os.path.join(basedir,'lib',osname,osver),
#               os.path.join(basedir,'lib',osname,osarch),
#               os.path.join(basedir,'lib',osname) ]

# commonlibdir = os.path.join(basedir, 'lib/common')
# chris 2004-09-02: lib/common/Extra/ holds 3rd party modules
# extralibdir = os.path.join(basedir, 'lib/common/Extra')
# sys.path = oslibdirs + [commonlibdir,extralibdir] + sys.path

# EDDIE common modules
from eddietool.common import parseConfig, directive, config, log, timeQueue, sockets, eddieElvin4, datacollect, utils, eddieSpread

# Main config file - this file INCLUDEs all other config files
# We set the default here, but this can be overridden on the command line
# configdir = os.path.join(basedir, 'config')
# default_config_file = os.path.join(configdir, 'eddie.cf')
# config_file = default_config_file

# Globals
global Config
global Options
global sthread
global cthread

# Read directive definitions from lib/common/Directives/
import eddietool.common.Directives
config.loadExtraDirectives(eddietool.common.Directives.__path__[0])

# Read system specific directives
# This is for directive modules in lib/<system>/Directives/ if it exists
#  for any <system>.
# for pth in oslibdirs:
#     subdir = os.path.join(pth, "Directives")
#     if os.path.isdir(subdir):
#         config.loadExtraDirectives(subdir)


def start_threads(sargs, cargs):
    """Start any support threads that are required.
    Currently these are:
     - Scheduler thread: schedules directives to run [required]
     - Console Server thread: handles connections to console port [optional]
    """

    please_die.clear()                # reset thread signal

    global sthread                # the Scheduler thread
    sthread = threading.Thread(group=None, target=scheduler, name='Scheduler', args=sargs, kwargs={})
    sthread.start()                 # start the thread running

    global cthread                # the Console Server thread
    if config.consport > 0:        # don't start if CONSPORT=0
        cthread = threading.Thread(group=None, target=sockets.console_server_thread, name='Console', args=cargs, kwargs={})
        cthread.setDaemon(1)        # mark thread as Daemon-thread so EDDIE will not block when trying to terminate
        cthread.start()

    return()


def stop_threads():
    """Stop any threads started by start_threads().
    """

    please_die.set()                # signal threads to die

    sthread.join()                # wait for scheduler thread to die

    if config.consport > 0:        # console thread not running if CONSPORT=0
        cthread.join()                # wait for console thread to die

    return()

 
def eddieexit():
    """Exit EDDIE cleanly.
    """

    log.log( '<eddie>eddieexit(): EDDIE exiting cleanly.', 5 )
    # email admin any remaining messages
    log.sendadminlog(1)
    sys.exit(0)


def SigHandler( sig, frame ):
    """Handle all the signals we are interested in.
    """

    global Options

    if 'SIGHUP' in dir(signal) and sig == signal.SIGHUP:
        # SIGHUP (Hangup) - reload config
        if not Options.daemon:
            print "SIGHUP - reloading config"
        log.log( '<eddie>SigHandler(): SIGHUP encountered - reloading config', 5 )

        stop_threads()

        # reset config and read in config and rules
        global Config
        Config = config.Config( '__main__' )

        # read in config and rules
        parseConfig.readConf(config_file, Config)

        # Initialise check queue
        q = timeQueue.timeQueue(0)                        # new timeQueue object, size is infinite
        buildCheckQueue(q, Config)
        Config.q = q

        sargs = (q, Config, please_die)
        cargs = (Config, please_die, config.consport)

        start_threads(sargs, cargs)

    elif 'SIGINT' in dir(signal) and sig == signal.SIGINT:
        # SIGINT (CTRL-c) - quit now
        log.log( '<eddie>SigHandler(): SIGINT (KeyboardInterrupt) encountered - quitting', 1 )
        log.log( '<eddie>SigHandler(): signalling scheduler thread to die', 6 )
        stop_threads()
        eddieexit()

    elif 'SIGTERM' in dir(signal) and sig == signal.SIGTERM:
        # SIGTERM (Terminate) - quit now
        log.log( '<eddie>SigHandler(): SIGTERM (Terminate) encountered - quitting', 1 )
        log.log( '<eddie>SigHandler(): signalling scheduler thread to die', 6 )
        stop_threads()
        eddieexit()

    elif 'SIGALRM' in dir(signal) and sig == signal.SIGALRM:
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
        except os.error, ( errnum, estr ):
            if errnum != errno.EBADF:
                #raise os.error, ( errnum, estr )
                log.log( '<eddie>countFDs(): exception os.error, %s, %s' %(errnum,estr), 5 )

    return fdcnt


def scheduler(q, Config, die_event):
    """The EDDIE scheduler thread.  This thread tracks the queue of waiting
    checks and executes them in their own thread as required.  It attempts
    to limit the number of actual checking threads running to keep things
    sane.
    """

    while not die_event.isSet():

        loop_start = time.time()        # get time when loop started
        while threading.activeCount() > config.num_threads:
            # do nothing while we have no active threads to play with
            # TODO: if we wait too long, something is probably wrong, so do something about it...
            log.log( "<eddie>scheduler(): active thread count is %d - waiting till <= %d" % (threading.activeCount(),config.num_threads), 8 )
            if time.time() - loop_start > 30*60:
                # if this loop has been running for over 30 mins, then all
                # threads are locked badly and something is wrong.  Force an
                # exit...
                # (there is no ability to kill threads in current Python implementation)
                log.log( "<eddie>scheduler(): active thread count has been %d for over %d mins - forcing exit" % (threading.activeCount(), (time.time()-loop_start)/60), 1 )
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
            (c,t) = q.head(block=1)        # wait for next object from queue
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

        (c,t) = q.get(block=1)        # retrieve next object from queue

        if c.args.numchecks > 0:
            # start check in a new thread
            thr = threading.Thread(group=None, target=c.safeCheck, name="%s"%(c), args=(Config,), kwargs={})
            log.log( "<eddie>scheduler(): Starting new thread for %s, %s" % (c,thr), 8 )
            thr.setDaemon(1)        # mark thread as Daemon-thread so EDDIE will not block when trying to terminate
                                    # with still-running threads.
            thr.start()                # new thread starts running
        else:
            # when numchecks == 0 we don't do any checks at all...
            log.log( "<eddie>scheduler(): Not scheduling checks for %s when numchecks=%d" % (c,c.args.numchecks), 7 )

    log.log( "<eddie>scheduler(): die_event received, scheduler exiting", 8 )


def buildCheckQueue(q, Config):
    """Build the queue of checks that the scheduler will start with.
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

    # chris 2004-09-20: throw away any domain parts of hostname; group names can't contain dots
    shorthostname = log.hostname.split('.')[0]

    # chris 2004-12-30: replace '-' with '_' for now...
    # TODO: this is a hack as group names in the config cannot contain '-'; this will
    # be resolved in the future when proper matching options are implemented fully.
    shorthostname = shorthostname.replace('-','_')

    for c in Config.groups:
        if c.name == shorthostname or (c.name in Config.classDict.keys() and shorthostname in Config.classDict[c.name]):
            log.log( "<eddie>buildCheckQueue(): Adding checks from group %s to queue" % (c.name), 7 )
            buildCheckQueue(q, c)
        else:
            log.log( "<eddie>buildCheckQueue(): Not queueing group %s" % (c.name), 8 )


def doArgs():
    """Parse command-line arguments.
    """
    # define usage and version messages
    usageMsg = "usage: %prog [options] eddie.cfg"
    versionMsg = """EDDIE Tool %s""" % __version__
    try:
        versionMsg += " (Build %s)" %'$Revision$'.split()[1]
    except:
        pass

    # get a parser object and define our options
    parser = optparse.OptionParser(usage=usageMsg, version=versionMsg)
    # parser.add_option('-c', '--config', dest='config',                 \
    #                     metavar="FILE", help="Load config from FILE")
    parser.add_option('--showconfig', action="store_true",
                        default=False,
                        help="Dump config")
    parser.add_option('-v', '--verbose', action="store_true",
                        default=False,
                        help="Enable verbose output")
    parser.add_option('-d', '--daemon', action="store_true",
                        default=False,
                        help="Run as a daemon")
    parser.add_option('-S', '--startup-delay', action='store', dest="startup_delay",        \
                        default=None, metavar="SECONDS",
                        help="Number of SECONDS to pause at startup before monitoring rule execution commences.")

    # Parse.  We dont accept arguments, so we complain if they're found.
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Configuration file must be given as first argument.')

    if options.startup_delay is not None:
        # Check value is acceptable
        try:
            value = int(options.startup_delay)
            if value < 0:
                raise ValueError()
        except:
            parser.error("-S|--startup-delay value must be a positive integer value.")
    
    # All good - return the option dict
    return (options, args[0])


def main():
    """Startup routine - setup then start main loop.
    """
    
    log.version = __version__        # Make version string available to other modules

    # Parse command-line arguments
    # instantiate global Options object
    global Options
    global config_file
    Options, config_file = doArgs()

    # Catch most important signals
    for sig in ('SIGALRM', 'SIGHUP', 'SIGINT', 'SIGTERM'):
        if sig in dir(signal):
            signal.signal( eval("signal.%s" %(sig)), SigHandler )

    # Get local hostname
    try:
        log.hostname = os.uname()[1]
    except AttributeError:
        try:
            import platform
            log.hostname = platform.node()
        except ImportError,msg:
            raise Exception( "Cannot determine hostname: %s" %(msg) )

    # instantiate global Config object
    global Config
    Config = config.Config( '__main__' )

    # data_modules handles access to all data collector modules
    data_modules = datacollect.DataModules(osname, osver, osarch)
    directive.data_modules = data_modules

    # read in config and rules
    parseConfig.readConf(config_file, Config)

    try:
        buildstr = " (Build %s)" %'$Revision$'.split()[1]
    except:
        buildstr = ''
    
    # don't log till now because log file location is defined in configuration
    log.log( "<eddie>main(): Configuration complete from '%s'" % (config_file), 6 )
    log.log( "<eddie>main(): EDDIE %s%s, systype: %s" % (__version__, buildstr, systype), 5 )
    log.log( "<eddie>main(): Python version: %s" % (sys.version), 5 )
    log.log( "<eddie>main(): oslibdirs: %s" % (data_modules.os_search_path), 8 )

    if Options.showconfig:
        # Just display the configuration and exit
        print "---Displaying EDDIE Configuration---"
        print Config
        eddieexit()

    if Options.startup_delay:
        delay = int(Options.startup_delay)
        if delay > 0:
            log.log( "<eddie>main(): pausing %d seconds before executing rules" %delay, 5)
            time.sleep(delay)
    
    if Options.daemon:
        # Create a child process, then have the parent exit
        cpid = utils.create_child(True)
        if cpid != 0:
            log.log( "<eddie>main(): Created child process %d. Parent exiting..." % (cpid), 6 )
            print cpid
            sys.exit(0)  # don't call eddieexit(), because its still running (as a daemon)

    # Initialise Elvin connections and thread to handle Elvin messaging
    try:
        elvin = eddieElvin4.Elvin()
    except eddieElvin4.ElvinInitError, details:
        log.log( "<eddie>main(): Elvin init failed, %s, Elvin functionality will be disabled."%(details), 5 )
        elvin = None
    else:
        elvin.startup()                # Start up the Elvin management thread
    Config.set_elvin(elvin)

    # Initialise Spread connection and thread to handle Spread messaging
    try:
        spread = eddieSpread.Spread()
    except eddieSpread.SpreadInitError, details:
        log.log( "<eddie>main(): Spread init failed, %s, Spread functionality will be disabled."%(details), 5 )
        spread = None
    else:
        spread.startup()                # Start up the Spread management thread
    Config.set_spread(spread)

    # Main Loop
    # Initialise check queue
    q = timeQueue.timeQueue(0)                        # new timeQueue object, size is infinite
    buildCheckQueue(q, Config)
    Config.q = q

    global please_die
    please_die = threading.Event()                # Event object to notify the scheduler to die
    global sthread

    sargs = (q, Config, please_die)
    cargs = (Config, please_die, config.consport)
    start_threads(sargs, cargs)

    while not please_die.isSet():
        try:
            ### Perform housecleaning duties

            # Count fds in use - for debugging
            #numfds = countFDs()
            #log.log( "<eddie>main(): FDs in use = %d." % (numfds), 8 )

            log.log( "<eddie>main(): Threads in use = %d." % (threading.activeCount()), 8 )
            log.log( "<eddie>main(): Threads: %s" % (threading.enumerate()), 8 )

            # check if any config/rules files have been modified
            # if so, re-read config
            if config.rescan_configs and Config.checkfiles():
                log.log( '<eddie>main(): config files modified - signalling scheduler to die', 7 )
                stop_threads()

                log.log( '<eddie>main(): config files modified - reloading config', 5 )

                # reset config and read in config and rules
                Config = config.Config( '__main__' )

                # read in config and rules
                parseConfig.readConf(config_file, Config)

                # Initialise check queue
                q = timeQueue.timeQueue(0)                        # new timeQueue object, size is infinite
                buildCheckQueue(q, Config)
                Config.q = q

                sargs = (q,Config,please_die)
                cargs = (Config, please_die, config.consport)
                start_threads(sargs,cargs)


            # email admin the adminlog if required
            log.sendadminlog()

            #time.sleep(10*60)        # sleep for 10 minutes between housekeeping duties
            please_die.wait(1*60)        # sleep for 1 minute between housekeeping duties
                                        # or until all threads signalled to exit

        except KeyboardInterrupt:
            # CTRL-c hit - quit now
            log.log( '<eddie>main(): KeyboardInterrupt encountered - quitting', 1 )
            eddieexit()


    log.log( '<eddie>main(): main thread signalled to die - exiting', 1 )
    eddieexit()




## agent-agent start point
def agent():
    try:
        main()
    
    except parseConfig.ConfigError:
        sys.exit(1)
    
    except:                # catch any uncaught exceptions so we can log them
        e = sys.exc_info()
        import exceptions
        if e[0] != exceptions.SystemExit:
            import traceback
            tb = traceback.format_list( traceback.extract_tb( e[2] ) )
            import string
            tbstr = string.join(tb, '')
            log.log( "<eddie.py>: EDDIE died with exception: %s, %s\n%s" % (e[0], e[1], tbstr), 1 )
            log.sendadminlog()
            sys.stderr.write( "EDDIE died with exception:" )
            sys.stderr.write( tbstr + '\n' )
            sys.stderr.write( str(e[0]) + '\n' + str(e[1]) + '\n' )
            sys.exit(1)


    # email admin anything else...
    log.sendadminlog()


