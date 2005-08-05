"""Provides an interface to the Win32 counter query API.

Requires Mark Hammond's win32all package.

doctests:

>>> wp = Win32Performance()
>>> wp							#doctest: +ELLIPSIS
<__main__.Win32Performance instance at 0x...>
>>> wp.addCounter( "System", "Context Switches/sec" )
>>> wp.addCounter( "System", "System Calls/sec" )
>>> wp.get()						#doctest: +ELLIPSIS
{'System System Calls/sec': ..., 'System Context Switches/sec': ...}
>>> wp.close()
>>> ctrs = getCounters('Network Interface')
>>> inst = getInstances('Network Interface')
>>> getDriveNames()					#doctest: +ELLIPSIS
[...'C:\\\\'...]
>>> getDriveNames(DRIVE_FIXED)				#doctest: +ELLIPSIS
['C:\\\\'...]
>>>
"""

__version__ = '1.0'
__author__ = 'Chris Miles'
__copyright__ = '(c) Chris Miles 2005'


### Python modules
import time
### Win32 modules
import pywintypes
import win32api
import win32file
import win32pdh


### Globals

DRIVE_FIXED = win32file.DRIVE_FIXED
DRIVE_CDROM = win32file.DRIVE_CDROM
DRIVE_REMOTE = win32file.DRIVE_REMOTE
DRIVE_REMOVABLE = win32file.DRIVE_REMOVABLE


### Classes

class Win32PerfError( Exception ):
    """Errors that occur with Win32Performance."""


class Win32Performance:
    """An interface to Win32 performance counters.
    Instantiate to open a query.
    Use addCounter() to add one or more counters.
    Use get() to fetch counter stats as a dictionary.

    Examples:
      wp.addCounter( "System", "Context Switches/sec" )
      wp.addCounter( "Processor", "% Processor Time", "_TOTAL" )
    """

    def __init__( self ):
	self.counters = []
	self.hq = win32pdh.OpenQuery()


    def addCounter( self, object, counter, instance=None ):
	"""Add a system performance counter.
	object is like "System", "Processor", etc.
	counter is like "Context Switches/sec"
	instance is optional, a numeric string, (eg "0") or "_TOTAL"
	"""

	try:
	    wcounter = Win32Counter( object, counter, instance )
	    wcounter.open( self.hq )
	except pywintypes.error:
	    raise Win32PerfError( "Cannot add counter ('%s', '%s', '%s')" %(object,counter,instance) )
	self.counters.append(wcounter)


    def get( self, pause=None ):
	"""Return a dictionary of all counters added by addCounter().
	If pause is set (positive integer) then wait this number of
	  seconds between two consequetive queries.  Some stats need
	  two queries so the result can be averaged.
	"""

	win32pdh.CollectQueryData( self.hq )
	if pause:
	    time.sleep( pause )
	    win32pdh.CollectQueryData( self.hq )

	perfvals = {}
	for c in self.counters:
	    val = c.getValue()
	    perfvals[c.name] = val
	return perfvals


    def close( self ):
	win32pdh.CloseQuery( self.hq )


class Win32Counter:
    """Holds information about one instance of a counter.
    """

    def __init__( self, object, counter, instance=None, machine=None ):
	self.object = object
	self.counter = counter
	self.instance = instance
	self.machine = machine
	self.inum = -1
	self.path = None
	self.hc = None

	self.name = "%s %s" %(object, counter)
	if instance:
	    self.name = self.name + " %s" %(instance)


    def open( self, hq ):
	"""Open a counter request from an already open win32pdh query.
	"""

	self.path = win32pdh.MakeCounterPath( (self.machine, self.object, self.instance, None, self.inum, self.counter) )
	self.hc = win32pdh.AddCounter( hq, self.path )


    def close( self ):
	"""Remove the counter request from the win32pdh query.
	"""

	win32pdh.RemoveCounter( self.hc )


    def getValue( self, format=win32pdh.PDH_FMT_LONG ):
	"""Return the value of the counter.
	"""

	type, val = win32pdh.GetFormattedCounterValue(self.hc, format)
	return val


### Module functions

def getCounters( object ):
    """Return a list of counter names that are available for
    a given win32pdh object name.

    Example:
    getCounters('Network Interface')
    ['Bytes Total/sec', 'Packets/sec', 'Packets Received/sec', 'Packets Sent/sec', 'Current Bandwidth', 'Bytes Received/sec', 'Packets Received Unicast/sec', 'Packets Received Non-Unicast/sec', 'Packets Received Discarded', 'Packets Received Errors', 'Packets Received Unknown', 'Bytes Sent/sec', 'Packets Sent Unicast/sec', 'Packets Sent Non-Unicast/sec', 'Packets Outbound Discarded', 'Packets OutboundErrors', 'Output Queue Length']
    """

    counters, instances = win32pdh.EnumObjectItems(None, None, object, win32pdh.PERF_DETAIL_WIZARD)
    return counters


def getInstances( object ):
    """Return a list of instances names that are available for
    a given win32pdh object name.

    Example:
    getInstances('Network Interface')
    ['ORiNOCO Wireless LAN Mini PCI Card - Packet Scheduler Miniport', 'Intel[R] PRO_100 Network Connection - Packet Scheduler Miniport', 'MS TCP Loopback interface']
    """

    counters, instances = win32pdh.EnumObjectItems(None, None, object, win32pdh.PERF_DETAIL_WIZARD)
    return instances


def getDriveNames( filter=None ):
    """Return a list of all mounted drive names on the current system.
    Restrict to drives of a certain type(s) using filter which should
    be an integer or a tuple of integers.  The DRIVE_* globals should
    be used as values for filter.

    Examples:
    > win32perf.getDriveNames()
    ['C:\\', 'D:\\', 'F:\\']
    > win32perf.getDriveNames(win32perf.DRIVE_FIXED)
    ['C:\\', 'D:\\']
    > win32perf.getDriveNames(win32perf.DRIVE_REMOTE)
    []
    > win32perf.getDriveNames(win32perf.DRIVE_REMOVABLE)
    ['F:\\']
    > win32perf.getDriveNames(filter=(win32perf.DRIVE_FIXED,win32perf.DRIVE_REMOVABLE))
    ['C:\\', 'D:\\', 'F:\\']
    """

    if type(filter) == type(1):
	filter = (filter,)	# convert to tuple of one value
    elif filter:
	try:
	    filter = tuple(filter)
	except TypeError:
	    raise SyntaxError('filter must be a tuple or integer')

    allDrives = [drive for drive in win32api.GetLogicalDriveStrings().split("\x00") if drive != '']

    if filter:
	return [drive for drive in allDrives if win32file.GetDriveType(drive) in filter]
    else:
	return allDrives



## doctest:
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
