
'''
File		: ack.py 

Start Date	: 20000124

Description	: Acknowledgement objects to track problem acknowledgements.

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2000-2005'

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
