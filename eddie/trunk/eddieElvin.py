#!/opt/local/bin/python
## 
## File         : eddieElvin.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980407
## 
## Description  : Elvin messaging interface
##
## $Id$
##

################################################################

import time, types, os, sys, thread, signal, getopt
import log
sys.path = ['/import/src/bin/elvin/dstc/lib/python', '/import/src/bin/elvin/dstc/sparc-sun-solaris2.5/lib'] + sys.path
import Elvin, ElvinMisc

################################################################
ElvinError = 'ElvinError'


class eddieElvin:

    def __init__(self, host, port):
	#self.host = 'chintoo'
	#self.port = 5678
	self.host = host
	self.port = port

	try:
	    self.elvin = Elvin.Elvin(Elvin.EC_NAMEDHOST, self.host, self.port,
				     None, self._error_cb)
	except:
	    #sys.stderr.write("Connection to elvin failed\nIs there an elvin server running at %s:%d\n" %(self.host, self.port))
	    #self._exit()
	    raise elvinError, "Connection failed to %s:%d" % (self.host,self.port)
	else:
	    self.connected = 1


    def sendmsg(self,msg):
	if self.connected:
	    self.elvin.notify( { 'TICKERTAPE' : 'Eddie',
	                         'TICKERTEXT' : msg,
				       'USER' : log.hostname,
				    'TIMEOUT' : 10, 
				  'MIME_TYPE' : x-elvin/slogin,
				  'MIME_ARGS' : log.hostname } )
	    return 0

	else:
	    #sys.stderr.write("Not connected when at notify time\n")
	    return 1

    def _exit(self):
	"""Exit routine. Because the thing that created us is
	sitting on a signal.pause. We signal ourselves to die"""
    
	os.kill(os.getpid(), signal.SIGUSR1)


    def _error_cb(self, code, msg):
	"""Elvin error callback. We reconnect"""

	sys.stderr.write("Elvin has gone ... will atempt to reconnect\n")
	self.connected = 0
	self._destroy()
	backoff = 4
	while not self._reconnect():
	    time.sleep(backoff)
	    backoff = backoff * 2
	    if backoff > 36000: # 10 mins
		sys.stderr.write("Elvin is really dead.  Giving up\n")
		os.kill(os.getpid(), signal.SIGUSR1)

    def _reconnect(self):
	"""Do the reconnection"""

	try:
	    sys.stderr.write(" Reconnecting at %s\n"%(time.ctime(time.time()),))
	    self.elvin = Elvin.Elvin(Elvin.EC_NAMEDHOST, self.host, self.port,
				None, self._error_cb)
	except:
	    sys.exc_traceback = None
	    return 0

	sys.stderr.write("New Elvin connection established\n")
	self.connected = 1
	return 1

    def _destroy(self):
	"""Clobber the internal elvin state so we can be deleted"""
	self.elvin.set_error_cb(None)
	self.elvin.set_quench_cb(None)
	del self.elvin
    
def _cleanup(sig, stackframe):
    """Performs any cleanup before exiting"""

    #print "_cleanup exiting on signal %d" %(sig,)
    ElvinMisc.ElvinRemovePidFile(pidname)
    sys.exit(0)

if __name__ == "__main__":

    e = eddieElvin()
    e.sendmsg("blah")

    sys.exit(0)



