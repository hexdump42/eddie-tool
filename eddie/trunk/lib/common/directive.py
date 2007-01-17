
'''
File                : directive.py 

Start Date        : 19971205 

Description        :

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



# Imports: Python
import string, re, sys, time, traceback
# Imports: Eddie
import action, utils, log, ack, history


##
## Define exceptions
##

# ParseFailure: a problem occured parsing the directive definition or the
#   directive arguments.  Config parsing will halt and an error will be
#   printed, pointing out the config line where parsing stopped.
ParseFailure = 'ParseFailure'

# DirectiveError: a critical error was caught while executing the directive.
#   The directive will not be re-scheduled for future execution.
DirectiveError = 'DirectiveError'


##
## Directive management objects
##

class State:
    """
    Object to track the state of a directive.
    """

    def __init__(self, thisdirective):
        self.ID = None                        # each directive has a unique ID
        self.lastfailtime = None        # last time a failure was detected
        self.faildetecttime = None        # first time failure was detected for current problem
        self.ack = ack.ack()                # ack object to track acknowledgements
        self.checkcount = 0                # count number of checks/re-checks
        self.failcount = 0                # count number of continuous failed checks
        self.thisdirective = thisdirective        # pointer to the directive this object belongs to

        # status holds the status of the most recent check.
        # Values can be:
        #   ok          - no problem
        #   failinitial - possible failure state (might need more rechecks, for example)
        #   fail        - check has failed
        #   unknown     - not executed yet
        # Initial value cannot be 'ok' because of 'checkdependson' race-condition.
        self.status = 'unknown'   # Status of most recent check.


    def ack(self, user=None, details=None):
        """Record a user acknowledgement for current problem."""

        self.ack.set(user, details)                # set the acknowledgement


    def statefail(self):
        """Update state info for check failure."""

        timenow = time.localtime(time.time())

        # is this a transition from "ok" to "fail" ?
        # Include "unknown" to get the faildetecttime, etc., behavior
        if self.status in ("ok", "unknown"):
            # if this is not a repeated failure then record the time of this
            # first failure detection
            self.faildetecttime = timenow
            self.failcount = 0                # re-initialize count of consecutive failures

            self.status = "failinitial"

        self.checkcount = self.checkcount + 1

        if self.checkcount >= self.thisdirective.args.numchecks:
            # Only put in "fail" state when all rechecks have failed
            # otherwise the state is left in "failinitial" state
            self.status = "fail"
            self.failcount = self.failcount + 1

        self.lastfailtime = timenow

        log.log( "<directive>State.statefail(): ID '%s' status '%s' checkcount %d lastfailtime %s faildetecttime %s"%(self.ID, self.status, self.checkcount, self.lastfailtime, self.faildetecttime), 7 )

        #TODO: Post an EVENT about this failure...
        #      EVENTS are either: new failure/problem detected
        #                     or: repeating failure


    def stateok(self, Config):
        """Update state info for check succeeding.
        Perform actions depending on previous state."""

        # is this a transition from "fail" to "ok" ?
        if self.status == "fail":
            # This is a state change from "fail" to "ok".
            # This is when the 'act2ok' actions should be performed.
            #
            # (If state was "failinitial" then check never really failed
            #  properly so allow change back to "ok" silently.)

            # Mark the lastfailtime as now, as state has been failed up until
            # this point in time.
            timenow = time.localtime(time.time())
            self.lastfailtime = timenow

            log.log( "<directive>State.stateok(): State changed to OK.  ID '%s'."%(self.ID), 7 )

            if 'act2okList' in dir(self.thisdirective.args):
                # chris 2003-10-03: only perform act2ok action if any actions were called.
                #        In cases where check fails but actiondependson causes actions to
                #        be skipped, we don't need the act2ok actions to be called.
                if self.thisdirective.performedactions:
                    self.thisdirective.performAction(Config,self.thisdirective.args.act2okList)
                else:
                    log.log( "<directive>State.stateok(): act2ok actions skipped as no actions were called.", 8 )

            #TODO: Post an EVENT about problem being resolved

        else:
            # If state wasn't previously failed then it is still ok.
            # This is when the 'actelse' actions should be performed.
            if 'actelseList' in dir(self.thisdirective.args):
                self.thisdirective.performAction(Config,self.thisdirective.args.actelseList)

        self.status = "ok"

        self.checkcount = 0                # reset check counter
        self.failcount = 0                # reset fail count
        self.thisdirective.current_actionperiod = 0        # reset the current actionperiod
        self.thisdirective.Action.runcount = 0        # chris 2002-12-29: reset action run counter
        self.thisdirective.performedactions = 0        # chris 2003-10-03: clear actions called flag

        log.log( "<directive>State.stateok(): ID '%s' status '%s'"%(self.ID, self.status), 7 )


    def age(self):
        """Length of time since problem first found and problem last detected.
           (ie: faildetecttime and lastfailtime).  Returned as time 9-tuple."""

        t1 = time.mktime(self.faildetecttime)
        t2 = time.mktime(self.lastfailtime)

        td = t2 -t1

        t0 = time.gmtime(0)                        # time base (ie: 1/1/1970)
        t9 = time.gmtime(td)                        # time diff from time base as 9-tuple
        tdiff = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # 9-tuple for time diff from 0

        for i in range(len(t0)):
            tdiff[i] = t9[i] - t0[i]

        return tdiff



class Args:
    """Container for holding directive arguments."""

    def __init__(self):
        """Nothing to do really."""
        pass



class Directive:
    """
    The base directive class.  All directives are derived from this base class.
    """

    def __init__(self, toklist):
        # Check toklist for valid tokens
        if len(toklist) < 2:                # need at least 2 tokens
            raise ParseFailure, "Directive expected at least 2 tokens, found %d" % len(toklist)
        if len(toklist) > 3:                # no more than 3 tokens
            raise ParseFailure, "Directive expected no more than 3 tokens, found %d" % len(toklist)
        if toklist[-1] != ':':                # last token should be a ':'
            raise ParseFailure, "Directive expected ':' but didn't find one"

        self.ID = None                        # No ID by default
        if len(toklist) == 3:
            self.ID = utils.stripquote(toklist[1])        # grab ID if given

        self.basetype = 'Directive'        # the object can know its own basetype
        self.type = toklist[0]                # the directive type of this instance

        self.request_collector()        # request data collector reference

        self.hastokenparser = 1                # tell parser this object has a separate tokenparser()

        self.Action = action.action()        # create new action instance
        self.defaultVarDict = {}        # dictionary of variables used by action strings

        self.args = Args()                # Container for arguments
        #self.args.actionList = []        # each directive will have a list of actions
        #self.args.act2okList = []        # a list of actions for failed state changing to ok
        #self.args.actelseList = []        # a list of actions for state remaining ok

        # Set up informational variables - these are common to all Directives
        #  %(hostname)s = hostname
        #  %(h)s = hostname                (shorthand for '%(hostname)s')
        self.defaultVarDict['hostname'] = log.hostname
        self.defaultVarDict['h'] = log.hostname

        # Create initial variable dictionary
        self.Action.varDict = {}

        # Set default output displayed on console connections
        self.console_output = '%(state)s'

        # List of directives this directive is dependent on
        self.actiondependson = []        # action dependencies
        self.checkdependson = []        # check dependencies

        # directives keep state information about themselves
        self.state = State(self)

        self.requeueTime = None        # specific requeue time can be specified

        self.args.numchecks = 1        # perform only 1 check at a time by default
        self.args.checkwait = 0        # time to wait in between multiple checks
        self.args.template = None        # no template by default
        self.args.disabled = False        # default "disabled" state to not disabled
        self.current_actionperiod = 0        # reset the current actionperiod
        self.lastactiontime = 0                # time previous actions were called

        self.history_size = 0        # keep no history by default
        self.history = None        # keep historical data for checks, if required

        self.excludehosts = []        # chris 2002-12-24: hosts to exclude from directive execution
        self.actionmaxcalls = None        # chris 2002-12-24: can set limit on number of action calls
        self.performedactions = 0        # chris 2003-10-03: clear actions called flag


    def request_collector(self):
        """
        If data collector(s) required, get reference(s) to it(them).
        If data collectors don't exist, the directive cannot be created.

        Data collectors are requested by creating a list of (module, collector)
        pairs in self.need_collectors.
        """

        self.data_collectors = {}        # dictionary of data collector references

        # If need_collectors is not defined, then no collectors are required,
        # just return to continue setting up directive
        try:
            self.need_collectors
        except:
            return 1                # ok

        for i in self.need_collectors:
            (module, collector) = i

            try:
                self.data_collectors["%s.%s"%(module,collector)] = data_modules.request( module, collector )
            except data_modules.DataModuleError:
                e = sys.exc_info()
                log.log( "<directive>Directive.request_collector(): error requesting %s.%s, %s %s" % (module,collector,e[0],e[1]), 1 )
                raise ParseFailure, "Error requesting collector %s.%s for directive %s:\n%s\n%s" % (module,collector,self.ID,e[0],e[1])

        return 1                # ok


    def __repr__( self ):
        return "%s" % (self.ID)


    def getDirective( self, ID, Config, norecurse=0 ):
        """getDirective: find the directive specified by ID, searching
        the current group first, then recursing the parent groups if
        not found.  Return None if not found.

        Set norecurse=1 if recursing parent groups is not required.
        """

        for d in Config.groupDirectives.keys():
            if ID == Config.groupDirectives[d].ID:
                return Config.groupDirectives[d]

        if Config.parent and norecurse==0:
            return self.getDirective( ID, Config.parent )

        return None


    def getGroup( self, groupname, Config ):
        """getGroup: find the group specified by groupname, searching
        the current group first, then recursing the parent groups if
        not found.  Return None if not found.
        """

        for g in Config.groups:
            if g.name == groupname:
                return g

        if Config.parent:
            return self.getGroup( groupname, Config.parent )

        return None


    def findDirective( self, ID, Config ):
        """findDirective: find a directive specified by ID, and optionally
        by group.

        If specified by ID only, the directive is recursively searched for
        in the current group and all parent groups.

        If a group is specified, the directive is searched for in that group
        only.  The group is first searched for in the current group and
        recursively up the parent groups.

        E.g. 1: findDirective( 'router_ping', Config )
        E.g. 2: findDirective( 'routers.router_ping', Config )
        E.g. 3: findDirective( 'routers.router1.router_ping', Config )
        """

        if not '.' in ID:
            # No group specified, just search current and parent groups
            return self.getDirective( ID, Config )

        else:
            # group is specified
            lookfor = string.split(ID, '.')
            grp = self.getGroup( lookfor[0], Config )        # get base group
            if not grp:
                return None

            if len(lookfor) > 2:                        # find subsequent groups
                for g in lookfor[1:-1]:
                    if g in grp.groups:
                        grp = grp.groups[g]
                    else:
                        return None

            # now fetch the directive
            return self.getDirective( lookfor[-1], grp, norecurse=1 )


    def tokenparser(self, toklist, toktypes, indent):
        """
        Parse named arguments for directives.  All valid named
        arguments are saved in the objects as self.args.argname,
        eg: self.args.rule

        It is up to each directive to check the validity of the arguments.
        Each directive should first call this function with:
            apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

        Note: toktypes and indent are not used by this function and can
        be None.
        """

        # Get all directive arguments
        tokdict = self.parseArgs(toklist)

        # Process template arg first to inherit template arguments
        if 'template' in tokdict.keys():
            self.args.template = tokdict['template']        # template name
            del tokdict['template']
            if self.args.template != 'self':
                tpldirective = self.findDirective(self.args.template, self.Config)
                if tpldirective == None:
                    raise ParseFailure, "template '%s' not found." % (self.args.template)
                else:
                    # copy template directive arguments
                    for t in dir(tpldirective.args):
                        if t == 'template':
                            continue
                        try:
                            val = eval( 'tpldirective.args.%s' % (t) )
                            if type( val ) == type( 'STRING' ):
                                val = utils.typeFromString( val )
                            exec( 'self.args.%s = val' % (t) )
                        except:
                            raise ParseFailure, "Error parsing template argument '%s'" % (t)

        for t in tokdict.keys():
            # Use action parser for any of the action lists
            if t == 'act2ok':
                self.args.act2okList = self.parseAction( tokdict[t] )
            elif t == 'actelse':
                self.args.actelseList = self.parseAction( tokdict[t] )
            elif t == 'action':
                self.args.actionList = self.parseAction( tokdict[t] )

            else:
                # Not an action, so build directive argument list
                # to be parsed below.
                try:
                    val = tokdict[t]
                    if type( val ) == type( 'STRING' ):
                        val = utils.typeFromString( val )
                    exec( 'self.args.%s = val' % (t) )
                except:
                    raise ParseFailure, "Error parsing argument '%s'" % (t)

        # Parse rest of directive arguments

        try:
            self.args.scanperiod
        except AttributeError:
            pass
        else:
            # convert scanperiod to integer seconds if not already
            if type(self.args.scanperiod) != type(1):
                self.args.scanperiod = utils.val2secs( self.args.scanperiod )
                if self.args.scanperiod == None:
                    raise ParseFailure, "Invalid scanperiod: '%s'"%(self.args.scanperiod)
            self.scanperiod = self.args.scanperiod        # set the scanperiod

        try:
            self.actionperiod = self.args.actionperiod
        except AttributeError:
            self.actionperiod = 'scanperiod'        # actionperiod defaults to scanperiod

        # test numchecks argument is integer and >= 0
        if type(self.args.numchecks) != type(1):
            try:
                self.args.numchecks = int(self.args.numchecks)
            except ValueError:
                raise ParseFailure, "numchecks argument is not integer: '%s'"%(self.args.numchecks)
        if self.args.numchecks < 0:
            raise ParseFailure, "numchecks argument must be > 0: '%s'"%(self.args.numchecks)

        # convert checkwait to integer seconds if not already
        try:
            if type(self.args.checkwait) != type(1):
                self.args.checkwait = utils.val2secs( self.args.checkwait )
        except:
            raise ParseFailure, "checkwait argument has incorrect value '%s'"%(self.args.checkwait)

        # Set console_output if possible
        try:
            self.console_output = self.args.console
        except AttributeError:
            pass        # console argument not set, so leave as default

        # Set history if required
        try:
            self.history_size = int(self.args.history)
        except AttributeError:
            pass        # history argument not set, so leave as default
        except ValueError:
            raise ParseFailure, "history must be an integer: '%s'"%(self.history_size)
        else:
            self.history = history.History( self.history_size )

        # Set action dependents if given
        try:
            actiondepends_names = string.split(self.args.actiondependson, ',')
        except AttributeError:
            pass        # no dependents given
        else:
            for dep in actiondepends_names:
                d = string.strip(dep)
                directive = self.findDirective( d, self.Config )
                if directive:
                    self.actiondependson.append( directive )
                else:
                    raise ParseFailure, "Directive %s, referred to in actiondependson, not found"%(d)

        # Set check dependents if given
        try:
            checkdepends_names = string.split(self.args.checkdependson, ',')
        except AttributeError:
            pass        # no dependents given
        else:
            for dep in checkdepends_names:
                d = string.strip(dep)
                if d:
                    directive = self.findDirective( d, self.Config )
                    if directive:
                        self.checkdependson.append( directive )
                    else:
                        raise ParseFailure, "Directive '%s', referred to in checkdependson, not found"%(d)

        # chris 2002-12-24: excludehosts parameter to exclude specific hosts;
        #        Requires a comma-separated list of hostnames.
        try:
            excludehosts = string.split(self.args.excludehosts, ',')
        except AttributeError:
            pass        # no excludehosts given
        else:
            for host in excludehosts:
                self.excludehosts.append( string.strip(host) )

        # chris 2002-12-29: actionmaxcalls parameter to specify maximum number of
        #        times the action(s) will be called for a particular check in
        #        failed state.
        try:
            actionmaxcalls = int(self.args.actionmaxcalls)
        except AttributeError:
            pass        # no actionmaxcalls given
        except ValueError:
            raise ParseFailure, "actionmaxcalls must be an integer: '%s'"%(self.args.actionmaxcalls)
        else:
            if actionmaxcalls < 0:
                raise ParseFailure, "actionmaxcalls must be >= 0: %s"%(self.args.actionmaxcalls)
            self.actionmaxcalls = actionmaxcalls

        # Set any default action variables
        if 'rule' in dir(self.args):
            self.defaultVarDict['rule'] = str(self.args.rule)

        # For all of the scalar args defined in the config, populate the
        # defaultVarDict dictionary with them as "_xxx" name, unless they are
        # already defined (don't override existing elements).
        for a in dir(self.args):
            try:
                val = eval( 'self.args.%s' % (a) )
                if type( val ) in ( type('STRING'), type(1), type(1.1) ) and not self.defaultVarDict.has_key( '_'+a ):
                    self.defaultVarDict['_'+a] = val
            except:
                pass

        if self.args.template == 'self':
            # jump out of token parsing if this is a template only
            raise 'Template'


    def evalAction(self, actioncall):
        """
        Evaluate the given action call.
        """

        log.log( "<directive>Directive.evalAction(): calling action '%s'" % (actioncall), 9 )

        # Evaluate action in environment with alias-dictionary to auto
        # substitute any aliases
        actionEnv = {}                                # setup action environment
        actionEnv.update(self.Action.aliasDict)        # add all aliases

        if self.Action.msg:
            # Get M group needed for this action
            msgtree = string.split( self.Action.msg, '.' )
            M = self.Action.MDict[msgtree[0]]
            for m in msgtree[1:]:
                M = M[m]

            #DEBUG
            #print "self.Action.msg:",self.Action.msg
            #print "self.Action.level:",self.Action.level
            #print "self.Action.MDict:",self.Action.MDict
            #print "self.Action.MDict:proc:",self.Action.MDict['proc']
            #print "M:",M

            actionEnv.update(M.MDict)                        # add MSGs

        actionEnv['_Action'] = self.Action                # add Action object
        acall = "_Action.%s" % (actioncall)                # the string to be evaluated

        evalenv = {}
        evalenv.update(actionEnv)                        # copy actionEnv for eval()
        try:
            ret = eval( acall, {"__builtins__": {}}, evalenv )                # Call the Action
        except:
            # Handle any action evaluation exceptions neatly
            e = sys.exc_info()
            tb = traceback.format_list( traceback.extract_tb( e[2] ) )
            log.log( "<directive>Directive.evalAction(): Error evaluating %s: %s, %s, %s; actionEnv=%s" % (acall, e[0], e[1], tb, actionEnv), 5 )
            return

        # Update the action reports
        self.Action.actionReports[actioncall] = ret
        if ret == None:
            self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % (actioncall)
        elif ret == 0:
            self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % (actioncall)
        else:
            self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (actioncall, ret)


    def performAction(self, Config, actionList):

        # Set the 'action' variables with the expanded action list
        self.Action.varDict['act'] = 'The following actions were attempted:\n'
        self.Action.varDict['actnm'] = 'The following (non-email) actions were attempted:\n'
        #TODO:
        #for a in actionList:
        #    self.Action.varDict['act'] = self.Action.varDict['act'] + '\t' + a + '\n'
        #    if a[:5] != 'email':
        #        self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '\t' + a + '\n'

        self.Action.state = self.state
        self.Action.aliasDict = Config.aliasDict

        # Perform each action
        ret = None
        self.Action.actionReports = {}                # dict of actions and their return status
        for a in actionList:
            sre = re.compile( "([A-Za-z0-9_]+)\(([A-Za-z0-9_.]+),?([0-9]?)\)" )
            inx = sre.search( a )
            if inx == None:
                # Assume we have a simple action call (rather than a
                # notification definition.
                self.Action.msg = None
                self.evalAction( a )

            else:
                # Using a Notification object
                notif = inx.group(1)
                msg = inx.group(2)
                level = inx.group(3)
                if level == None or level == '':
                    level = '0'

                #print ">>>> notif:",notif
                #print ">>>> msg:",msg
                #print ">>>> level:",level

                try:
                    # Get the actions to execute from the given Level of the N object
                    afunc = Config.NDict[notif].levels[level]
                except KeyError:
                    log.log( "<directive>Directive.performAction(): Error in directive.py line 431: Config.NDict[notif].levels[level], level=%s" % level, 5 )
                else:
                    self.Action.notif = notif
                    self.Action.msg = msg
                    self.Action.level = level
                    self.Action.MDict = Config.MDict #TODO: move to init() ?

                    aList = utils.trickySplit( afunc[0], ',' )
                    # Put quotes around arguments so we can use eval()
                    #aList = utils.quoteArgs( aList )
                    for aa in aList:
                        self.evalAction( aa )


    def doAction(self, Config, actionList=None):
        """Perform actions for a directive."""
        
        if self.state.checkcount < self.args.numchecks:
            # need to wait before re-checking
            # when put back in queue only wait checkwait seconds
            self.requeueTime = time.time()+self.args.checkwait
            log.log( "<directive>doAction(): scheduling for recheck in %d seconds" % (self.args.checkwait), 6 )
            return
        else:
            self.state.checkcount = 0        # performing action so reset counter
  
        if self.state.failcount > 1:
            timewaited = time.time() - self.lastactiontime

            if timewaited < self.current_actionperiod:
                # If current_actionperiod has not passed between action calls
                # then wait a bit longer
                log.log( "<directive>doAction(): current_actionperiod (%s) not reached, actions not run" % (self.current_actionperiod), 6 )
                return

        # record action information
        self.lastactiontime = time.time()

        # Calculate action period
        log.log( "<directive>doAction(): self.state.failcount=%d" % self.state.failcount, 8 )
        if self.state.failcount == 1:
            # After first action call, action period defaults to scanperiod
            self.current_actionperiod = self.scanperiod
        else:
            # For subsequent action calls, evaluate actionperiod expression
            log.log( "<directive>doAction(): evaluate actionperiod '%s'" % self.actionperiod, 8 )
            evalenv = { 'scanperiod' : self.scanperiod,
                        't' : self.current_actionperiod }
            self.current_actionperiod = eval( self.actionperiod, {"__builtins__": {}}, evalenv )
        log.log( "<directive>doAction(): current_actionperiod=%d" % self.current_actionperiod, 8 )

        # Make sure there are some actions to perform
        # (they are not always necessary)
        if 'actionList' in dir(self.args):
            self.performedactions = 1        # chris 2003-10-03: flag that actions have been called
            self.performAction(Config, self.args.actionList)


    def parseAction(self, toklist):
        """Parses token list and returns a list of action call strings."""

        actstr = ""
        for t in toklist:
            if t != '\012':
                actstr = actstr + t
        actlist = utils.trickySplit( actstr, ',' )
        return actlist


    def parseArgs( self, toklist ):
        """
        Return dictionary of directive arguments.

        toklist is a list of directive argument lines.
        Each line is a list of basic tokens.
        Argument lines must be of the form: <name>=<value>
          where <name> is a 'word' and <value> is something like a string,
          int, float, function call, etc.
        """

        argdict = {}

        for argline in toklist:
            if len(argline) < 3 or argline[1] != '=':
                log.log( "<directive>Directive.parseArgs(): invalid directive argument '%s'" % (string.join(argline)), 1)
                raise ParseFailure, "invalid directive argument '%s'" %(string.join(argline))

            if len(argline) > 3:
                argdict[argline[0]] = utils.stripquote(string.join(argline[2:],""))
            else:
                argdict[argline[0]] = utils.stripquote(argline[2])

        return argdict


    def putInQueue( self, q ):
        """Put this directive back into the scheduler queue."""

        if self.requeueTime:
            # a specific requeueTime has been requested
            q.put( (self,self.requeueTime) )
            self.requeueTime = None
            log.log( "<directive>Directive.putInQueue(): %s re-queued by requeueTime" % (self), 7)

        else:
            # reschedule in scanperiod seconds
            q.put( (self, time.time()+self.scanperiod) )
            log.log( "<directive>Directive.putInQueue(): %s re-queued by scanperiod (%d secs)" % (self,self.scanperiod), 7)


    def doDirective( self, Config, data ):

        # If historical data is required
        if self.history:
            if self.history.getsize() < self.history_size:
                # If historical data is required for check, the directive
                # must wait until enough data is collected
                log.log( "<directive>Directive.doDirective(): waiting for %d runs to collect enough data for history" % (self.history_size), 7 )
                self.history.push( data )
                self.putInQueue( Config.q )        # put self back in the Queue
                return

            # Add historical data to data dictionary
            data['history'] = self.history

        # If data returned as None, do not perform a check but still
        # re-schedule directive.
        if data == None:
            self.putInQueue( Config.q )        # put self back in the Queue
            return

        # Populate the data dictionary with the defaultVarDict.
        # This get us, among other things, "_xxx" constants.
        data.update(self.defaultVarDict)

        try:
            #result = eval( self.args.rule, {"__builtins__": {}}, data )
            result = eval( self.args.rule, {}, data )
        except SyntaxError, details:
            # Syntax error evaluating rule. Log and end thread without
            # submitting broken directive back into queue.
            log.log( "<directive>Directive.doDirective(): SyntaxError evaluating rule '%s', data=%s - not re-queued" % (self.args.rule,data), 4 )
            return
        except NameError, details:
            # Name error evaluating rule. Log and end thread without
            # submitting broken directive back into queue.
            log.log( "<directive>Directive.doDirective(): NameError evaluating rule '%s', %s, data=%s - not re-queued" % (self.args.rule,details,data), 4 )
            return

        # Create action string substitution variables.
        # These are a dictionary of data-collection variables along with any
        # extra variables added specifically by the Directive itself.
        self.Action.varDict = {}
        #self.Action.varDict.update(self.defaultVarDict)
        self.Action.varDict.update(data)
        self.addVariables()

        if result == 0:
            self.state.stateok(Config)        # update state info for check passed

        else:
            self.state.statefail()        # update state info for check failed

            log.log( "<directive>Directive.doDirective(): %s rule failed, calling doAction()" % (self.ID), 7 )
            # If any dependencies are also failed, running actions for this
            # directive are not required.
            failed_deps = self.checkDependencies( self.actiondependson )
            if failed_deps:
                log.log( "<directive>Directive.doDirective(): dependencies %s failed, %s not calling actions" % (failed_deps, self.ID), 7 )
            else:
                if self.actionmaxcalls != None and self.Action.runcount >= self.actionmaxcalls:
                    log.log( "<directive>Directive.doDirective(): actionmaxcalls reached (%d) - actions skipped" % (self.actionmaxcalls), 7 )
                    self.putInQueue( Config.q )        # put self back in the Queue
                    return
                else:
                    self.doAction(Config)
                    self.Action.runcount = self.Action.runcount + 1
                    log.log( "<directive>Directive.doDirective(): Action.runcount=%d" % (self.Action.runcount), 9 )

        # Save historical data
        if self.history:
            del data['history']                        # Remove old history data
            self.history.push( data )

        self.postAction( data )                # perform any post-action processing

        self.putInQueue( Config.q )        # put self back in the Queue


    def safeCheck( self, Config ):
        """
        This function is called to start a new checking thread for a directive.
        It wraps the directive's self.docheck() in try/except so any un-caught
        exceptions can be captured (and logged) and the thread exited nicely.
        """

        log.log( "<directive>Directive.safeCheck(): ID '%s', calling self.docheck()" % (self.state.ID), 7 )

        if self.args.disabled:
            log.log( "<directive>Directive.safeCheck(): ID '%s', disabled" % (self.state.ID), 5 )
            return

        self.last_check_time = time.localtime(time.time())        # note time of last check

        try:
            self.docheck( Config )
        except:
            e = sys.exc_info()
            tb = traceback.format_list( traceback.extract_tb( e[2] ) )
            log.log( "<directive>Directive.safeCheck(): ID '%s', Uncaught exception: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )
            return

        log.log( "<directive>Directive.safeCheck(): ID '%s', self.docheck() returned successfully" % (self.state.ID), 7 )


    def docheck(self, Config):
        """
        Common Directive method to start executing the directive-specific check
        (or directive function, which may not necessarily "check" something)
        by calling the sub-class method self.getData() to fetch the necessary
        data which is then used as the environment to execute the directive
        rule in.
        
        If the rule evaluates to "true" (not 0 or None) the check is
        considered to have failed and the actions will be called.

        getData() should return a dictionary of variables to be used in the
        rule evaluation environment. The variables will also be added to the
        action variables list to be used in action strings.

        If getData() returns the None object, no check is to be performed in
        this instance, but directive will be re-scheduled.

        If getData() raises directive.DirectiveError, it is considered to have
        hit a critical error and the message will be logged and the directive
        discarded (not re-scheduled).
        """

        # CM 2003-09-10: If checktime specified, evaluate and don't run this
        #        directive if outside time rule specified
        if 'checktime' in dir(self.args):
            # Setup variables used to evaluate the checktime rule
            timevars = {}
            # get time() once, to prevent possible race condition
            ts = time.strftime('%a~%H%M~%H~%M~%S').lower().split('~')
            timevars['day']    = ts[0]
            timevars['time']   = int(ts[1])
            timevars['hour']   = int(ts[2])
            timevars['minute'] = int(ts[3])
            timevars['second'] = int(ts[4])
            timevars['weekdays'] = ('mon','tue','wed','thu','fri')
            timevars['weekend']  = ('sat','sun')

            try:
                result = eval( self.args.checktime, {}, timevars )
            except SyntaxError, details:
                # Syntax error evaluating rule. Log and end thread without
                # submitting broken directive back into queue.
                log.log( "<directive>Directive.docheck(): SyntaxError evaluating checktime '%s', %s, timevars=%s - not re-queued" % (self.args.checktime,details,timevars), 4 )
                return
            except NameError, details:
                # Name error evaluating rule. Log and end thread without
                # submitting broken directive back into queue.
                log.log( "<directive>Directive.docheck(): NameError evaluating checktime '%s', %s, timevars=%s - not re-queued" % (self.args.checktime,details,timevars), 4 )
                return

            if not result:
                # if checktime evaluates to false, then skip the check
                log.log( "<directive>Directive.docheck(): checktime false - skipping", 7 )
                return


        # If any check dependencies are failed, don't need to run this check
        failed_deps = self.checkDependencies( self.checkdependson )
        if failed_deps:
            log.log( "<directive>Directive.docheck(): dependencies %s failed, %s not checking" % (failed_deps, self.ID), 7 )
            self.putInQueue( Config.q )        # put self back in the Queue
            return

        # If this is the second or subsequent check of a re-check, refresh the data
        if self.state.checkcount > 0:
            for i in self.data_collectors.keys():
                self.data_collectors[i].refresh()        # force refresh of data if re-checking

        # self.getData() must be supplied by Directive sub-class.
        # It must fetch the required data (if any) somehow...
        # All fetched data should be returned in a dictionary.
        try:
            data = self.getData()
        except DirectiveError, err:
            # Critical directive error, log message and end directive thread.
            # (Directive will not be re-scheduled.)
            log.log( "<directive>Directive.docheck(): directive %s error, %s, not re-scheduled" % (self.ID,err), 4 )
            return

        self.doDirective( Config, data )


    def addVariables(self):
        """
        Add any directive-specific variables to the action variables
        dictionary.

        This function must be overloaded by the Directive sub-class, if
        required.
        By default it does nothing (simply an empty place-holder).
        """

        pass


    def postAction(self, data):
        """
        Perform any directive-specific post-action processing.
        It is passed the data dictionary.

        This function must be overloaded by the Directive sub-class, if
        required.
        By default it does nothing (simply an empty place-holder).
        """

        pass


    def console_str(self, str=None):
        """Return the string that is to be output on console connections."""

        if str == None:
            str = self.console_output

        if str == None:
            return None

        ## Setup variables available to console_output string
        vars = {}

        # If the action was never-ever called, we need to get those vars populated
        # (otherwise, Action.varDict should already contain all of defaultVarDict).
        vars.update(self.defaultVarDict)

        # add all the action variables
        vars.update(self.Action.varDict)

        # Note that if doDirective never got to execute the action, there can still be KeyError issues.

        # add the current state
        vars['state'] = self.state.status

        # add time of last check
        try:
            t = self.last_check_time
            vars['lastchecktime'] = "%04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        except AttributeError:
            vars['lastchecktime'] = "<not yet run>"

        # add the lastfailtime and faildetecttime
        if self.state.status == "fail":
            t = self.state.faildetecttime
            vars['problemfirstdetect'] = "First detected: %04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
            t = self.state.lastfailtime
            vars['problemlastfail'] = "Last detected: %04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        else:
            vars['problemfirstdetect'] = ""
            vars['problemlastfail'] = ""


        # create console string by substituting variables
        cstr = str % vars
        return cstr


    def checkDependencies(self, deplist):
        """checkDependencies: return a list of any failed directives which this
        directive is dependent on.  Pass dependency list as deplist.
        """

        failed = []
        for d in deplist:
            # "bad" status include 'fail', 'failinitial', and 'unknown'
            if d.state.status != 'ok':
                failed.append(d)

        return failed


##
## END - directive.py
##
