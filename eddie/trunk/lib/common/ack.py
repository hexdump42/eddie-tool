#!/opt/local/bin/python 
## 
## File		: ack.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 20000124
## 
## Description	: Acknowledgement objects to track problem acknowledgements.
##
## $Id$
##
##


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
