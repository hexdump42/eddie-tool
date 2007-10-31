
'''
File            : history.py 

Start Date      : 19980209 

Description  : Eddie historical data handler
    Example rule:
    rule="pctused - history[1].pctused > 10"        # pctused increased by over 10%

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 1998-2005'

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



import log,threading


# Container of data
class Hist:
    pass


# Store a list of historical data
class History:
    def __init__(self, size):
        self.size = size
        self.history = []
        self.history_semaphore = threading.Semaphore()


    def push(self, data):
        self.history_semaphore.acquire()        # Thread safety

        h = Hist()
        for d in data.keys():
            exec "h.%s = data[d]" % (d)
        self.history.insert(0, h)        # add new data to front of list
        if len(self.history) > self.size:
            self.history.pop()                # remove oldest data

        self.history_semaphore.release()

        log.log( "<history>History.push(): Added data %s"%(data), 8 )


    def getsize(self):
        return len(self.history)


    def __getitem__(self, index):
        if index < 1 or index > self.size:
            log.log( "<history>History.__getitem__(): index out of range %d"%(index), 4 )
            return None

        self.history_semaphore.acquire()        # Thread safety
        data = self.history[index-1]
        self.history_semaphore.release()
        log.log( "<history>History.__getitem__(): fetched history[%d]=%s"%(index,data), 8 )
        return data


    def __repr__(self):
        return "%s" % self.history

###
### END history.py
###
