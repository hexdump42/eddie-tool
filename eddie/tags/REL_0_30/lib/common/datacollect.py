## 
## File		: datacollect.py
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Date		: 20000520
## 
## Description	: The Eddie data collection parent class
##
## $Id$
##
########################################################################
## (C) Chris Miles 2002
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

# Python modules
import time, threading
# Eddie modules
import log


class DataModules:
    """
    This class keeps track of which data collection modules are required
    (directives request data collection modules as they are created);
    makes sure appropriate modules are available;
    and creates data collection objects as required.
    """

    DataModuleError = "DataModule Error"	# for exceptions

    def __init__(self):
	self.collectors = {}		# dictionary of collectors and their associated objects


    def request(self, module, collector):
	"""
	Directives request data collection objects and the modules they should
	be defined in.

	Return reference to collector object if successful;
	Return None if failed.
	"""

	# if collector already initiated, return reference
	if collector in self.collectors.keys():
	    return self.collectors[collector]

	try:
	    exec "import %s" % (module)
	except ImportError:
	    log.log( "<datacollect>DataModules.request(): error, collector '%s'/module '%s' not found or not available" % (collector,module), 3 )
	    raise self.DataModuleError, "Collector '%s', module '%s' not found or not available" % (collector,module)

	# initialise new collector instance
	initstr = "self.collectors[collector] = %s.%s()" % (module,collector)
	try:
	    exec initstr
	except AttributeError:
	    log.log( "<datacollect>DataModules.request(): error, no such collector '%s' in module '%s'" % (collector,module), 3 )
	    raise self.DataModuleError, "No such collector '%s' in module '%s'" % (collector,module)

	log.log( "<datacollect>DataModules.request(): collector %s/%s initialised" % (module,collector), 7 )

	return self.collectors[collector]


class Data:
    """
    An empty class to hold any data to be stored.
    Do not access this data without first acquiring DataCollect.data_semaphore
    for thread-safety.
    """

    pass


class DataHistory:
    """
    Store previous data, with up to max_level levels of history.
    Set max_level with setHistory() or else no data is kept.
    """

    def __init__(self):
	self.max_level = 0		# how many levels of data to keep
	self.historical_data = []	# list of historical data (newest to oldest)


    def setHistory(self, level):
	"""
	Set how many levels of historical data to keep track of.
	By default no historical data will be kept.

	The history level is only changed if the level is greater than
	the current setting.  The history level is always set to the highest
	required by all directives.
	"""

	if level > self.max_level:
	    self.max_level = level


    def __getitem__(self, num):
	"""
	Overloaded [] to return the historical data, num is the age of the data.
	num can be 0 which is the current data; 1 is the previous data, etc.
	e.g., d = history[5]
	would assign d the Data object from 5 'collection periods' ago.
	"""

	try:
	    data = self.historical_data[num]
	except IndexError:
	    raise IndexError, "DataHistory index out-of-range: index=%d" % (num)

	return data


    def update(self, data):
	"""
	Update data history by adding new data object to history list
	and removing oldest data from list.

	If max_level is 0, no history is required, so nothing is done.
	"""

	if self.max_level > 0:
	    if len(self.historical_data) > self.max_level:
		# remove oldest data
		self.historical_data = self.historical_data[:-1]

	    self.historical_data.insert(0, data)


    def length(self):
	"""
	Returns the current length of the historical data list;
	i.e., how many samples have been collected and are stored in the list.
	"""

	# Subtract 1 from len as the first sample in list is always the current sample
	return len(self.historical_data) - 1
	


class DataCollect:
    """
    Provides a data collection and store class with automatic
    caching and refreshing of data in the cache.  Public functions
    are fully thread-safe as they can be called from many directive
    threads simultaneously.

    Data is cached for 55 seconds by default.  Assign self.refresh_rate
    to change this.  A collectData() function must be supplied by any
    child class of DataCollect.  This function should get data by
    whatever means and assign it to variables in self.data.

    Historical data will be automatically kept by calling setHistory(n)
    with n>0.  n levels of historical data will then be automatically
    kept.  If setHistory() is called multiple times, the highest n will
    stay in effect.

    Public functions are:
     getHash()	- return a copy of a data dictionary
     getList()	- return a copy of a data list
     hashKeys()	- return list of data dictionary keys
     __getitem__() - use DataCollect object like a dictionary to fetch data
     refresh()	- force a cache refresh
     setHistory(n) - set max level (n) of data history to automatically keep
    """

    def __init__(self):
	self.refresh_rate = 55	# amount of time current information will be
	                        # cached before being refreshed (in seconds)

	self.refresh_time = 0	# information must be refreshed at first request

	self.history_level = 0	# how many levels of historical data to keep
	self.history = DataHistory()	# historical data
	self.data_semaphore = threading.Semaphore()	# lock before accessing self.data/refresh_time

	#self.data = Data()	# object for storing collected data


    ##################################################################
    # Public, thread-safe, methods

    def getHash(self, hash='datahash'):
        """
	Return a copy of the specified data hash, datahash by default.
	Specify an alternate variable name to fetch it instead.

	TODO: it might be better to use the 'copy' module to make sure
	 a full deep copy is made of the date...
	"""

        self._checkCache()      	# refresh data if necessary
	dh = {}
        self.data_semaphore.acquire()	# thread-safe access to self.data
        exec 'dh.update(self.data.%s)'%(hash)	# copy data hash
        self.data_semaphore.release()

        return(dh)


    def hashKeys(self):
        """Return the list of datahash keys."""

        self._checkCache()      	# refresh data if necessary
        self.data_semaphore.acquire()	# thread-safe access to self.data
        k = self.data.datahash.keys()
        self.data_semaphore.release()

        return(k)


    def getList(self, listname):
        """
	Return a copy of the specified data list.
	The function is thread-safe and supports the built-in data caching.

	TODO: it might be better to use the 'copy' module to make sure
	 a full deep copy is made of the date...
	"""

        self._checkCache()      	# refresh data if necessary
        self.data_semaphore.acquire()	# thread-safe access to self.data
        exec 'list_copy = self.data.%s[:]'%(listname)	# copy data list
        self.data_semaphore.release()

        return(list_copy)


    def __getitem__(self, key):
        """
        Overload '[]', eg: returns corresponding data object for given key.

	TODO: it might be better to use the 'copy' module to make sure
	 a full deep copy is made of the date...
        """

        self._checkCache()              # refresh data if necessary

        self.data_semaphore.acquire()	# thread-safe access to self.data
        try:
            r = self.data.datahash[key]
        except KeyError:
	    self.data_semaphore.release()
            raise KeyError, "Key %s not found in data hash" % (key)
        self.data_semaphore.release()

        return r


    def refresh(self):
	"""
	Refresh data.

	This function can be called publically to force a refresh.
	"""

	self.data_semaphore.acquire()	# thread-safe access to self.data
	log.log( "<datacollect>DataCollect.refresh(): forcing data refresh", 7 )
	self._refresh()
	self.data_semaphore.release()


    def setHistory(self, level):
	"""
	Set how many levels of historical data to keep track of.
	By default no historical data will be kept.

	The history level is only changed if the level is greater than
	the current setting.  The history level is always set to the highest
	required by all directives.
	"""

	self.history.setHistory(level)



    #############################################################################
    # Private methods.  Thread safety not guaranteed if not using public methods.

    def _checkCache(self):
	"""Check if cached data is invalid, ie: refresh_time has been exceeded."""

	self.data_semaphore.acquire()		# thread-safe access to self.refresh_time and self._refresh()
	if time.time() > self.refresh_time:
	    log.log( "<datacollect>DataCollect._checkCache(): refreshing data", 7 )
	    self._refresh()
	else:
	    log.log( "<datacollect>DataCollect._checkCache(): using cached data", 7 )
	self.data_semaphore.release()


    def _refresh(self):
	"""
	Refresh data by calling _fetchData() and increasing refresh_time.

	This function must be called between data_semaphore locks. It is
	not thread-safe on its own.
	"""

	self._fetchData()

        # new refresh time is current time + refresh rate (seconds)
        self.refresh_time = time.time() + self.refresh_rate


    def _fetchData(self):
	"""
	Initialise a new data collection by first resetting the current data,
	then calling self.collectData() - a user-supplied function, see below -
	then storing historical data if necessary.

	Derivatives of this base class must define a collectData() method which
	should collect any data by whatever means and store that data in the
	self.data object.  It can be assumed all appropriate thread-locks are
	in place so access to self.data will be safe.
	"""

	self.data = Data()		# new, empty data-store

	self.collectData()		## user-supplied function to collect some data
					## and store in self.data

	self.history.update(self.data)	# add collected data to history




##
## END - datacollect.py
##
