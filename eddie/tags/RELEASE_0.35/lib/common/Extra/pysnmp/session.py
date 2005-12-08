"""
   SNMP v.1 engine class.

   Sends & receives SNMP v.1 messages.

   Written by Ilya Etingof <ilya@glas.net>, 1999, 2000, 2001

"""
import socket
import select

# Import package components
import message
import error

class session (message.message):
    """Build & send SNMP request, receive & parse SNMP response
    """
    def __init__ (self, agent, community='public'):
        # Call message class constructor
        message.message.__init__ (self, community)

        # Make sure we get all these arguments
        if not agent:
            raise error.BadArgument ('Empty SNMP agent name')

        # Initialize SNMP session
        self.agent = agent
        self.port = 161
        self.timeout = 1.0
        self.retries = 3
        self.iface = None

        # This is a provision for multisession superclass
        self.request = None
        self.response = None

        # Initialize socket
        self.socket = None

    def store (self, request):
        """
           store(message)
           
           Store SNMP message for later transmission.
        """
        if not request:
            raise error.BadArgument('Empty SNMP message')

        # Otherwise, store the message to be sent
        self.request = request

    def get_socket (self):
        """
           get_socket() -> socket

           Return socket object previously created with open() method.
        """
        return self.socket

    def open (self):
        """
           open()
           
           Initialize transport layer (UDP socket) to be used
           for further communication with remote SNMP process.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        except socket.error, why:
            raise error.TransportError('socket() error: ' + str(why))

        # See if we need to bind to specific interface at SNMP
        # manager machine
        if self.iface:
            try:
                self.socket.bind((self.iface[0], 0))

            except socket.error, why:
                raise error.TransportError('bind() error: ' + str(why))

        try:
            self.socket.connect((self.agent, self.port))

        except socket.error, why:
            raise error.TransportError('connect() error: ' + str(why))

        return self.socket

    def send (self, request=None):
        """
           send([message])
           
           Send SNMP message (the specified one or previously submitted
           with store() method) to remote SNMP process specified on
           session object creation.
        """
        # Message must present
        if not request and not self.request:
            raise error.BadArgument('Empty SNMP message')

        # Make sure we are given a message
        if request:
            # Store new request            
            self.store (request)

        # Make sure the connection is established, open it otherwise
        if not self.socket:
            self.open()

        try:
            self.socket.send(self.request)

        except socket.error, why:
            raise error.TransportError('send() error: ' + str(why))

    def read (self):
        """
           read() -> message
           
           Read data from the socket (assuming there's some data ready
           for reading), return SNMP message (as string).
        """   
        # Make sure the connection exists
        if not self.socket:
            raise error.NotConnected

        try:
            self.response = self.socket.recv(65536)

        except socket.error, why:
            raise error.TransportError('recv() error: ' + str(why))

        return self.response
        
    def receive (self):
        """
           receive() -> message
           
           Receive SNMP message from remote SNMP process or timeout
           (and return None).
        """
        # Initialize sockets map
        r, w, x = [self.socket], [], []

        # Wait for response
        r, w, x = select.select(r, w, x, self.timeout)

        # Timeout occurred?
        if r:
            try:
                self.response = self.socket.recv(65536)

            except socket.error, why:
                raise error.TransportError('recv() error: ' + str(why))

            return self.response

        # Return nothing on timeout
        return None

    def send_and_receive (self, message):
        """
           send_and_receive(message) -> message
           
           Send SNMP message to remote SNMP process (as specified on
           session object creation) and receive a response message
           or timeout (and raise NoResponse exception).
        """
        # Initialize retries counter
        retries = 0

        # Send request till response or retry counter hits the limit
        while retries < self.retries:
            # Send a request
            self.send (message)

            # Wait for response
            response = self.receive ()

            # See if it's succeeded
            if response:
                return response

            # Otherwise, try it again
            retries = retries + 1

        # No answer, raise an exception
        raise error.NoResponse('No response arrived before timeout')

    def close (self):
        """
           close()
           
           Close UDP socket used to communicate with remote SNMP agent.
        """
        # See if it's opened
        if self.socket:
            try:
                self.socket.close()

            except socket.error, why:
                raise error.TransportError('close() error: ' + str(why))

            # Initialize it to None to indicate it's closed
            self.socket = None  
