# encoding: utf-8

'''linux_diskio
'''

__author__ = 'Chris Miles'
__copyright__ = '(c) Chris Miles 2006'
__id__ = '$Id$'
__url__ = '$URL$'
__version__ = '1.0'


# ---- Imports ----

# - Python Modules -
import os
import unittest


# ---- Globals ----

PROC_DISKSTATS  = '/proc/diskstats'
PROC_PARTITIONS = '/proc/partitions'

# From what I've found elsewhere:
# "The sectors are equivalent with blocks and have a size of 512 bytes since 2.4
# kernels. This value is needed to calculate the amount of disk i/o's in bytes."
SECTOR_SIZE = 512


# ---- Exceptions ----

class LinuxDiskIOError(Exception):
    '''Error with LinuxDiskIO.
    '''


# ---- Classes ----

class LinuxDiskIO(object):
    '''Return disk I/O statistics for a disk device.
    A devicename is something like "sda", "sda1", "cciss/c0d0", etc...
    '''
    def __init__(self, devicename, sector_size=SECTOR_SIZE):
        self.devicename = devicename
        self.sector_size = sector_size

    def getStats(self):
        if os.path.exists(PROC_DISKSTATS):
            return self._getStatsProcDiskstats()
        elif os.path.exists(PROC_PARTITIONS):
            return self._getStatsProcPartitions()
        else:
            raise LinuxDiskIOError("Cannot find any disk I/O kernel files: %s" %((PROC_DISKSTATS,PROC_PARTITIONS)))

    def _getStatsProcDiskstats(self):
        stats = None
        fp = file(PROC_DISKSTATS)
        for line in fp:
            if len(line) > 1:
                fields = line.split()
                assert len(fields) in (7, 14)
                if len(fields) == 14:
                    (major, minor, name, rio, rmerge, rsect, ruse, wio, wmerge, wsect, wuse, running, use, aveq) = fields
                    if name == self.devicename:
                        stats = {
                            'rio'       : int(rio),
                            'rmerge'    : int(rmerge),
                            'rbytes'    : int(rsect) * self.sector_size,
                            'ruse'      : int(ruse),
                            'wio'       : int(wio),
                            'wmerge'    : int(wmerge),
                            'wbytes'    : int(wsect) * self.sector_size,
                            'wuse'      : int(wuse),
                            'running'   : int(running),
                            'use'       : int(use),
                            'aveq'      : int(aveq),
                        }
                elif len(fields) == 7:
                    (major, minor, name, rio, rsect, wio, wsect) = fields
                    if name == self.devicename:
                        stats = {
                            'rio'       : int(rio),
                            'rbytes'    : int(rsect) * self.sector_size,
                            'wio'       : int(wio),
                            'wbytes'    : int(wsect) * self.sector_size,
                        }
        fp.close()
        return stats


    def _getStatsProcPartitions(self):
        stats = None
        fp = file(PROC_PARTITIONS)
        fp.next()       # skip header line
        for line in fp:
            if len(line) > 1:
                fields = line.split()
                assert len(fields) == 15
                (major, minor, blocks, name, rio, rmerge, rsect, ruse, wio, wmerge, wsect, wuse, running, use, aveq) = fields
                if name == self.devicename:
                    stats = {
                        'rio'       : int(rio),
                        'rmerge'    : int(rmerge),
                        'rbytes'    : int(rsect) * self.sector_size,
                        'ruse'      : int(ruse),
                        'wio'       : int(wio),
                        'wmerge'    : int(wmerge),
                        'wbytes'    : int(wsect) * self.sector_size,
                        'wuse'      : int(wuse),
                        'running'   : int(running),
                        'use'       : int(use),
                        'aveq'      : int(aveq),
                    }
        fp.close()
        return stats


# ---- Module functions ----

def get_device_names():
    '''Return a list of all the device names that
    have I/O statistics available for them.
    '''
    if os.path.exists(PROC_DISKSTATS):
        fp = file(PROC_DISKSTATS)
        fieldindex = 2
    elif os.path.exists(PROC_PARTITIONS):
        fp = file(PROC_PARTITIONS)
        fp.next()       # skip header
        fieldindex = 3
    else:
        raise LinuxDiskIOError("Cannot find any disk I/O kernel files: %s" %((PROC_DISKSTATS,PROC_PARTITIONS)))

    device_names = []
    for line in fp:
        if len(line) > 1:
            device_names.append(line.split()[fieldindex])
    fp.close()
    return device_names



# ---- Unit tests ----

class LinuxDiskIOProcPartitionsTests(unittest.TestCase):
    def setUp(self):
        global PROC_DISKSTATS
        global PROC_PARTITIONS
        PROC_DISKSTATS = 'tests/no_such_file'
        PROC_PARTITIONS = 'tests/proc_partitions.txt'
        self.disk_sda = LinuxDiskIO('sda')

    def testType(self):
        self.failUnlessEqual(type(self.disk_sda), LinuxDiskIO)

    def testStats(self):
        self.failUnlessEqual(
            self.disk_sda.getStats(),
            {
                'rio'       : 120830,
                'rmerge'    : 88344,
                'rbytes'    : 1632316 * SECTOR_SIZE,
                'ruse'      : 855650,
                'wio'       : 276487,
                'wmerge'    : 385541,
                'wbytes'    : 5301850 * SECTOR_SIZE,
                'wuse'      : 10689920,
                'running'   : 0,
                'use'       : 1165580,
                'aveq'      : 11560430,
            }
        )


class LinuxDiskIOProcDiskstatsTests(unittest.TestCase):
    def setUp(self):
        global PROC_DISKSTATS
        global PROC_PARTITIONS
        PROC_DISKSTATS = 'tests/proc_diskstats.txt'
        PROC_PARTITIONS = 'tests/no_such_file'
        self.disk_c0d0 = LinuxDiskIO('cciss/c0d0')
        self.disk_c0d0p1 = LinuxDiskIO('cciss/c0d0p1')

    def testType(self):
        self.failUnlessEqual(type(self.disk_c0d0), LinuxDiskIO)

    def testStats_c0d0(self):
        self.failUnlessEqual(
            self.disk_c0d0.getStats(),
            {
                'rio'       : 457990,
                'rmerge'    : 18390,
                'rbytes'    : 9929666 * SECTOR_SIZE,
                'ruse'      : 14602120,
                'wio'       : 11994332,
                'wmerge'    : 33737665,
                'wbytes'    : 366986508 * SECTOR_SIZE,
                'wuse'      : 2303150201,
                'running'   : 402,
                'use'       : 77318476,
                'aveq'      : 2320700244,
            }
        )

    def testStats_c0d0p1(self):
        self.failUnlessEqual(
            self.disk_c0d0p1.getStats(),
            {
                'rio'       : 6304,
                'rbytes'    : 12616 * SECTOR_SIZE,
                'wio'       : 2,
                'wbytes'    : 4 * SECTOR_SIZE,
            }
        )
    

class DeviceNamesProcPartitionsTests(unittest.TestCase):
    def setUp(self):
        global PROC_DISKSTATS
        global PROC_PARTITIONS
        PROC_DISKSTATS = 'tests/no_such_file'
        PROC_PARTITIONS = 'tests/proc_partitions.txt'
        self.device_names = get_device_names()

    def testDeviceNames(self):
        self.failUnlessEqual(self.device_names, ['sda', 'sda1', 'sda2', 'sda5', 'sda6', 'sdb', 'sdb1', 'sdb5'])


class DeviceNamesProcDiskstatsTests(unittest.TestCase):
    def setUp(self):
        global PROC_DISKSTATS
        global PROC_PARTITIONS
        PROC_DISKSTATS = 'tests/proc_diskstats.txt'
        PROC_PARTITIONS = 'tests/no_such_file'
        self.device_names = get_device_names()

    def testDeviceNames(self):
        self.failUnlessEqual(self.device_names, ['ram0', 'ram1', 'ram2', 'ram3', 'ram4', 'ram5', 'ram6', 'ram7', 'ram8', 'ram9', 'ram10', 'ram11', 'ram12', 'ram13', 'ram14', 'ram15', 'hda', 'cciss/c0d0', 'cciss/c0d0p1', 'cciss/c0d0p2', 'dm-0', 'dm-1', 'dm-2', 'fd0', 'md0'])



if __name__ == '__main__':
    unittest.main()
