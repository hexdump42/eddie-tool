#!/opt/local/bin/python 
## 
## File		: ack.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Date		: 20000124
## 
## Description	: Acknowledgement objects to track problem acknowledgements.
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2001
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



# Imports: Python
import time


class ack:
    """The ack(nowledgement) class to keep state of last acknowledgement."""

    def __init__(self):
	self.clear()


    def clear(self):
	"""Clear all acknowledgement information."""

	self.state = "n"	# acknowledged or not, "y" or "n"
	self.time = None	# time of acknowledgement
	self.user = None	# user who acknowledged
	self.details = None	# other details


    def set(self, user=None, details=None):
	"""Set a user acknowledgement."""

	self.clear()		# clear any previous ack first

	self.state = "y"	# acknowledged
	self.time = time.localtime(time.time())
	self.user = user
	self.details = details


##
## END - ack.py
##
