#!/opt/python2/bin/python
## 
## File         : estored
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 20010823
## 
## Description  : Elvin4 consumer to insert Eddie STORE data into a database.
##
## $Id$
##

################################################################

__version__ = """$Revision$"""[11:-2]

################################################################

import os, sys, signal, time, traceback
import MySQLdb	# requires MySQLdb module from http://dustman.net/andy/python/MySQLdb
import elvin	# requires Elvin4 modules from http://elvin.dstc.edu.au/

ELVIN_URL='elvin://elvin.connect.com.au'
ELVIN_SCOPE='elvin'
MYSQL_HOST = 'localhost'
MYSQL_DB = 'eddiedata'

################################################################

class eddieElvin:

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	self.elvinurl = elvinurl
	self.elvinscope = elvinscope

	if self.elvinurl and len(self.elvinurl) > 0:
	    connect_string=self.elvinurl
	elif self.elvinscope and len(self.elvinscope) > 0:
	    connect_string=self.elvinscope
	else:
	    connect_string='*'		# auto discovery

	print "Trying Elvin connection to %s" % (connect_string)

	try:
	    self.elvinc = elvin.connect( connect_string )
	    print "Elvin connection succeeded."
	except:
	    sys.stderr.write("Connection to elvin failed - connection string was '%s'\n" % (connect_string) )
	    sys.exit(1)

	print "Connecting to MySQL server %s:%s" % (MYSQL_HOST, MYSQL_DB)
	self.dbcon = MySQLdb.connect(host=MYSQL_HOST, db=MYSQL_DB)
	self.dbcur = self.dbcon.cursor()
	print "MySQL connecting established"


    def cleanExit(self):
	self.dbcon.close()	# close database connection
	self.elvinc.close()	# close Elvin connection


class storeconsumer(eddieElvin):

    def __init__(self, elvinurl=ELVIN_URL, elvinscope=ELVIN_SCOPE):
	apply( eddieElvin.__init__, (self, elvinurl, elvinscope) )


    def register(self):

	#self.subscription = 'exists(ELVIN.COMMAND)'
	# ** above won't work as the Elvin parser refuses to parse an exists()
	# expression with a '.' in the string.... grrr...

	self.subscription = 'require(ELVINDB)'

	sub=self.elvinc.subscribe(self.subscription)
	sub.add_listener(self.deliver)
	sub.register()


    def deliver(self, sub, msg, insec, rock):
 
	#print "msg:", msg

	del msg['ELVINDB']	# throw this away - only there for exists() above.

	cols = "timestamp, hostname, "
	values = "'%s', '%s', " % (msg['ELVIN.TIMESTAMP'],msg['ELVIN.HOST'])
	for d in msg.keys():
	    if d[:6] != 'ELVIN.':
		cols = cols + d + ', '
		if type(msg[d]) == type("") or type(msg[d]) == type(u""):	# string or unicode string
		    values = values + "'%s', " % (msg[d])
		elif type(msg[d]) == type(1):
		    values = values + "%d, " % (msg[d])
		elif type(msg[d]) == type(1.0):
		    values = values + "%f, " % (msg[d])
		elif type(msg[d]) == type(1L):
		    values = values + "%ld, " % (msg[d])
		else:
		    values = values + "%s, " % (msg[d])

	# throw away ', ' from end of strings
	if len(cols) > 2:
	    cols = cols[:-2]
	if len(values) > 2:
	    values = values[:-2]

	#print "cols:",cols
	#print "values:",values

	cmd = 'INSERT INTO %s (%s) VALUES (%s)' % (msg['ELVIN.TABLE'], cols, values)
	print "cmd:",cmd

	## DEBUGGING
	#if msg['ELVIN.TABLE'] == 'pop3timing':
	#    print "cmd:",cmd
	#print
	#print ".",
	#print msg['ELVIN.TABLE'][:4],
	#sys.stdout.flush()

	try:
	    r = self.dbcur.execute( cmd )
	except:
            e = sys.exc_info()
            tb = traceback.format_list( traceback.extract_tb( e[2] ) )
            print "Exception during dbcur.execute() for cmd '%s'\n  %s, %s, %s" % (cmd, e[0], e[1], tb)
	else:
	    if r != 1:
                print "r=%d for dbcur.execute(), cmd '%s'" % (r, cmd)



if __name__ == "__main__":

    e = storeconsumer()
    e.register()
    e.elvinc.run()



###
### End of estored
###
