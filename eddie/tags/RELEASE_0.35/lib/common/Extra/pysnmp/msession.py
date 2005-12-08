"""
   SNMP v.1 engine class.

   Sends & receives many SNMP v.1 messages in bulk.

   Written by Ilya Etingof <ilya@glas.net>, 1999, 2000, 2001

"""
import socket
import select

# Import package components
import session
import message
import error

class multisession (message.message):
    """Perform multiple SNMP queries virtually simultaneously
    """
    def __init__ (self):
        # Set defaults to public attributes
        self.retries = 3
        self.timeout = 1
        self.iface = None

        self.initialize ()
        
    def initialize (self):
        """Reset private class instance variables to get ready
        """
        # [Re-]create a list of active sessions
        self.sessions = []

    def submit_request (self, agent, community='public',\
                        type='GETREQUEST',\
                        encoded_oids=[], encoded_vals=[]):
        """
           submit_request(agent[, community[, type[,\
                          encoded_oids[, encoded_vals]]]]):
        
           Create SNMP message of specified "type" (default is GETREQUEST)
           to be sent to "agent" with SNMP community name "community"
           (default is public) and loaded with encoded Object IDs
           "encoded_oids" along with their associated values "encoded_values"
           (default is empty lists).

           New SNMP message will be added to a queue of SNMP requests to
           be transmitted to their destinations (see dispatch()).
        """
        # Create new SNMP session
        ses = session.session (agent, community)

        # Pass options to this session
        ses.iface = self.iface

        # Build a SNMP message
        message = ses.encode_request(type, encoded_oids, encoded_vals)

        # Store the message to be sent in the session object
        ses.store (message)

        # Add it to the list of active sessions
        self.sessions.append(ses)

    def dispatch (self):
        """
           dispatch()
           
           Send pending SNMP requests and receive replies (or timeout).
        """
        # Reset session response attribute for all sessions saved
        # in the multisession as dispatcher() may be called several times
        for ses in self.sessions:
            ses.response = None

        # Initialize retries counter
        retries = 0

        # Try to get responses from all the agents
        while retries < self.retries:
            # Initialize sockets map
            r, w, x = [], [], []

            # Send out requests and prepare for waiting for replies
            for ses in self.sessions:
                # Skip completed session
                if ses.response:
                    continue

                try:
                    # Try to create SNMP session and send 
                    # the message
                    ses.open()
                    ses.send()

                    # Add this session's socket into the sockets map
                    r.append(ses.socket)
                    
                except error.SNMPEngineError:
                    pass

            # Collect responses from agents
            while r:
                # Wait for response
                r1, w1, x1 = select.select(r, w, x, self.timeout)

                # If timeout occurred
                if not r1:
                    retries = retries + 1
                    break
                    
                # Scan through the list of ready sockets 
                for sock in r1:
                    # Find corresponding socket
                    for ses in self.sessions:
                        # Skip sockets that have already responded
                        if ses.response:
                            continue
                        
                        # See if response arrived for this session
                        if ses.socket == sock:
                            try:
                                # Read up data from the socket
                                ses.read ()

                            except error.SNMPEngineError:
                                # Indicate a failure
                                ses.response = None

                            # Close this session
                            ses.close ()

                            # Take this socket off the list of sockets
                            # we select on
                            r.remove(sock)
                            
                            # Assume there are no duped sessions in the
                            # list of sessions
                            break

            # When we read from all sockets, we are done
            else:
                break

        # Close all the sockets
        for ses in self.sessions:
            # It's harmless to close() already closed session
            ses.close ()

    def retrieve (self):
        """
           retrieve() -> [(encoded_oids, encoded_vals), ...]
           
           Retrieve previously received SNMP repsponses as a list of pairs
           of encoded Object IDs along with their associated values
           (unsuccessful, timed out requests will return a tuple of
           empty lists).

           The order of responses in the list is guaranteed to be the same
           as requests SNMP requests were submitted (see submit_request()).
        """
        results = []
        
        # Walk over the list of responses
        for ses in self.sessions:
            # Assume the session has failed and there is no SNMP
            # response to parse so there will be empty response
            # to return
            encoded_pairs = ([], [])

            # Try to decode response for this session if present
            if ses.response:
                try:
                    encoded_pairs = ses.decode_response(ses.response)

                except error.SNMPError:
                    # SNMP errors lead to empty responses
                    pass

            # Append response to the list of responses
            results.append(encoded_pairs)

        # Terminate existing SNMP sessions
        self.sessions = []
 
        return results
