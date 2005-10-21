## 
## File		: diskdevice.py 
## 
## Author       : Chris Miles - http://chrismiles.info/
## 
## Start Date	: 20051021
## 
## Description	: Eddie-Tool data collector for Linux disk
##		  activity statistics.
##
## $Id$
##
########################################################################
## (C) Chris Miles 2005
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

"""
  **TODO: this is currently a place-holder - it does not yet do anything.**

  This is an Eddie data collector.  It collects disk & tape -usage
  statistics.

  The DataCollectors provided are:
    DiskStatistics : collects statistics about disk devices
    TapeStatistics : collects statistics about tape devices
"""


# Python modules
import os
import string
# Eddie modules
import datacollect
import log
import utils


##
## Globals
##


##
## Exceptions
##
 

##
## Classes
##

class DiskStatistics(datacollect.DataCollect):
    """Collects disk statistics. TODO
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	# *TODO*
	self.data.datahash = {}

        log.log( "<diskdevice>DiskStatistics.collectData(): *not yet implemented*", 5 )



class TapeStatistics(datacollect.DataCollect):
    """Collects tape statistics. TODO
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	# *TODO*
	self.data.datahash = {}

        log.log( "<diskdevice>TapeStatistics.collectData(): *not yet implemented*", 5 )


##
## END - diskdevice.py
##
