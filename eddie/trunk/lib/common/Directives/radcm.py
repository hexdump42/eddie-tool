#!/usr/bin/env python
"""
radcm - A Python Radius client module
(c) Chris Miles <chris@psychofx.com> 20001016

$Id$
$Source$

(Based on code by Stuart Bishop <zen@cs.rmit.edu.au>)
"""

import sys,getopt, getpass, select, struct, whrandom, md5, socket, time

# Constants
ACCESS_REQUEST	= 1
ACCESS_ACCEPT	= 2
ACCESS_REJECT	= 3

DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 5

class Error(Exception): pass
class NoResponse(Error): pass
class SocketError(NoResponse): pass

def authenticate(username,password,secret,host='radius',port=1645):
    '''Return 1 for a successful authentication. Other values indicate
       failure (should only ever be 0 anyway).

       Can raise either NoResponse or SocketError'''

    r = Radius(secret,host,port)
    return r.authenticate(username,password)

class Radius:

    def __init__(self,server,secret,auth_port=1645,acct_port=1646,timeout=DEFAULT_TIMEOUT,retries=DEFAULT_RETRIES):
	if server == None or server == '':
	    raise 'Radius.error', 'Server host not specified'
	if secret == None or secret == '':
	    raise 'Radius.error', 'Secret not specified'

	self.server = server
	self.secret = secret
	self.auth_port = auth_port
	self.acct_port = acct_port

	self.retries = retries
	self.timeout = timeout
	self.socket = None


    def __del__(self):
	self.closesocket()


    def opensocket(self):
	if self.socket == None:
	    self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	    self.socket.connect((self.server,self.auth_port))


    def closesocket(self):
	if self.socket is not None:
	    self.socket.close()
	self.socket = None


    def generateAuthenticator(self):
	"""A 16 byte random string"""
	v = range(0,17)
	v[0] = '16B'
	for i in range(1,17):
	    v[i] = whrandom.randint(1,255)

	return apply(struct.pack,v)


    def radcrypt(self,authenticator,text,pad16=0):
	"""Encrypt a password with the secret"""

	md5vec = md5.new(self.secret + authenticator).digest()
	r = ''

	# Encrypted text is just an xor with the above md5 hash,
	# although it gets more complex if len(text) > 16
	for i in range(0,len(text)):

	    # Handle text > 16 characters acording to RFC
	    if (i % 16) == 0 and i <> 0:
		md5vec = md5.new(self.secret + r[-16:]).digest()

	    r = r + chr( ord(md5vec[i]) ^ ord(text[i]) )

	# When we encrypt passwords, we want to pad the encrypted text
	# to a multiple of 16 characters according to the RFC
	if pad16:
	    for i in range(len(r),16):
		r = r + md5vec[i]
	return r


    def authenticate(self,uname,passwd):
	"""Attempt to authenticate with the given username and password.
	   Returns 0 on failure
	   Returns 1 on success
	   Raises a NoResponse (or its subclass SocketError) exception if 
		no responses or no valid responses are received"""

	try:
	    self.opensocket()
	    id = whrandom.randint(0,255)

	    authenticator = self.generateAuthenticator()

	    encpass = self.radcrypt(authenticator,passwd,1)
	    
	    msg = struct.pack('!B B H 16s B B %ds B B %ds' \
		    % (len(uname),len(encpass)),\
		1,id,
		len(uname)+len(encpass) + 24, # Length of entire message
		authenticator,
		1,len(uname)+2,uname,
		2,len(encpass)+2,encpass)

	    for i in range(0,self.retries):
		self.socket.send(msg)

		t = select.select( [self.socket,],[],[],self.timeout)
		if len(t[0]) > 0:
		    # Hmm... I should look up the correct max reply length?
		    response = self.socket.recv(1024)
		else:
		    continue

		if ord(response[1]) <> id:
		    continue

		# Verify the packet is not a cheap forgery or corrupt
		checkauth = response[4:20]
		m = md5.new(response[0:4] + authenticator + response[20:] 
		    + self.secret).digest()

		if m <> checkauth:
		    continue

		if ord(response[0]) == ACCESS_ACCEPT:
		    return 1	
		else:
		    return 0

	except socket.error,x: # SocketError
	    try:
		self.closesocket()
	    except:
		pass
	    raise SocketError(x)

	raise NoResponse


if __name__ == '__main__':

    # defaults
    server = 'localhost'
    auth_port = 1645
    acct_port = 1646
    secret = ''
    timeout = 5

    small_args = 's:S:p:P:u:w:d:n:t:'
    big_args = ['server=', 'secret=', 'auth_port=', 'acct_port=', 'user=', 'password=', 'dictionary=', 'nas_port=', 'timeout=']
    optlist, args = getopt.getopt(sys.argv[1:], small_args, big_args)

    for o in optlist:
	if o[0] == '--server' or o[0] == '-s':
	    server = o[1]
	if o[0] == '--secret' or o[0] == '-S':
	    secret = o[1]
	if o[0] == '--auth_port' or o[0] == '-p':
	    auth_port = int(o[1])
	if o[0] == '--acct_port' or o[0] == '-P':
	    acct_port = int(o[1])
	if o[0] == '--user' or o[0] == '-u':
	    user = o[1]
	if o[0] == '--password' or o[0] == '-w':
	    password = o[1]
	if o[0] == '--dictionary' or o[0] == '-d':
	    dictionary = o[1]
	if o[0] == '--nas_port' or o[0] == '-n':
	    nas_port = int(o[1])
	if o[0] == '--timeout' or o[0] == '-t':
	    timeout = int(o[1])

    r = Radius(server,secret,auth_port)

    tstart = time.time()
    try:
	z = r.authenticate(user,password)
    except NoResponse:
	z = None
    tend = time.time()

    if z:
	print "Authentication Succeeded"
    else:
	print "Authentication Failed"

    print "Took %f seconds." % (tend - tstart)


