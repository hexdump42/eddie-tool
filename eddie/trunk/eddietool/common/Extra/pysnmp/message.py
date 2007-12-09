"""
   SNMP v.1 engine class.

   Assembles & disassembles SNMP v.1 message.

   Written by Ilya Etingof <ilya@glas.net>, 1999, 2000, 2001

"""
import types
import random

# Import package components
import ber
import error

class message (ber.ber):
    """BER encode & decode SNMP message
    """
    def __init__ (self, community='public', version=0):
        if not community:
            raise error.BadArgument('Bad community name')

        if type(version) != types.IntType:
            raise error.BadArgument('Bad SNMP version: ' + str(version))

        self.request_id = long (random.random()*0x7fffffff)
        self.version = version
        self.community = community

    #
    # ENCODERS
    #

    def encode_bindings (self, encoded_oids, encoded_values):
        """
            encode_bindings(encoded_oids, encoded_values) -> bindings
            
            Bind together encoded object IDs and their associated values
            (lists of strings).
        """
        # Get the number of oids to encode
        size = len(encoded_oids)

        # Make sure the list is not empty
        if not size:
            raise error.BadArgument('Empty list of encoded Object IDs')

        # Initialize stuff
        index = 0
        encoded_oid_pairs = ''

        # Encode encoded objid's and encoded values together
        while index < size:
            # Encode and concatinate one oid_pair
            if encoded_values and encoded_values[index]:
                # Merge oid with value
                oid_pairs = encoded_oids[index] + \
                            encoded_values[index]
            else:
                # Merge oid with value
                oid_pairs = encoded_oids[index] + \
                            self.encode_null()

            # Encode merged pairs
            encoded_oid_pairs = encoded_oid_pairs + \
                self.encode_sequence (oid_pairs)

            # Progress index
            index = index + 1

        # Return encoded bindings
        return self.encode_sequence(encoded_oid_pairs)

    def encode_snmp_pdu (self, type, bindings):
        """
           encode_snmp_pdu (self, type, bindings) -> SNMP PDU

           Encode PDU type (string) and variables bindings (string) into
           SNMP PDU.
        """
        self.request_id = self.request_id + 1

        return self.encode_snmp_pdu_sequence (type, \
               self.encode_integer(self.request_id) + \
               self.encode_integer(0) + \
               self.encode_integer(0) + \
               bindings)

    def encode_request_sequence (self, pdu):
        """
           encode_request_sequence(pdu) -> SNMP message
           
           Encode SNMP version, community name and PDU into SNMP message
        """
        return self.encode_sequence ( \
               self.encode_integer (self.version) + \
               self.encode_string (self.community) + \
               pdu)

    def encode_request (self, type, encoded_oids, encoded_values):
        """
           encode_request(type, encoded_oids, encoded_values) -> SNMP message
           
           Encode Object IDs and values (lists of strings) into variables
           bindings, then encode bindings into SNMP PDU (of specified type
           (string)), then encode SNMP PDU into SNMP message.
        """
        return self.encode_request_sequence (\
               self.encode_snmp_pdu (type,\
               self.encode_bindings (encoded_oids, encoded_values)))

    def encode_snmp_trap_pdu (self, enterprise, addr, generic, specific,
                              timeticks, bindings):
        """
           encode_snmp_trap_pdu (enterprise, addr, generic, specific,
                                 timeticks, bindings) -> SNMP TRAP PDU
                                 
           Encode enterpise Object-ID (given as a list of integer subIDs),
           agent IP address (string), generic trap type (integer), specific
           trap type (integer), timeticks (integer) and variable bindings
           (string) into SNMP Trap-PDU (see RFC-1157 for details)
        """
        return self.encode_snmp_pdu_sequence ('TRAPREQUEST', \
               self.encode_oid(enterprise) + \
               self.encode_ipaddr(addr) + \
               self.encode_integer(generic) + \
               self.encode_integer(specific) + \
               self.encode_timeticks(timeticks) + \
               bindings)
        
    def encode_trap (self, enterprise, addr, generic, specific, timeticks,
                     encoded_oids=[], encoded_values=[]):
        """
           encode_trap(enterprise, addr, generic, specific, timeticks[,
                       encoded_oids, encoded_values]) -> SNMP message
                                 
           Encode enterpise Object-ID (list of integer sub-IDs), agent IP
           address (string), generic trap type (integer), specific trap
           type (integer), timeticks (integer) along with Object IDs and their
           values into SNMP message (lists of strings).

           See RFC-1157 for details.
        """
        # Encode variables bindings if given
        if encoded_oids:
            bindings = self.encode_bindings (encoded_oids, encoded_values)
        else:
            bindings = ''
            # XXX
#            result = '0\0'
    
        return self.encode_request_sequence ( \
               self.encode_snmp_trap_pdu (enterprise, addr, generic,
                                          specific, timeticks, bindings))

    #
    # DECODERS
    #

    def decode_response_sequence (self, message):
        """
           decode_response_sequence(message) -> (version, community, PDU)
           
           Parse SNMP message (string), return SNMP protocol version used
           (integer), community name (string) and SNMP PDU (string).
        """
        # Unwrap the whole packet
        packet = self.decode_sequence (message)

        # Decode SNMP version
        length, size = self.decode_length (packet[1:])
        version = self.decode_integer (packet)
    
        # Update packet index
        index = size + length + 1

        # Decode community
        length, size = self.decode_length (packet[index+1:])
        community = self.decode_string (packet[index:])

        # Update packet index
        index = index + size + length + 1

        # Return SNMP version, community and PDU
        return (version, community, packet[index:])

    def decode_bindings (self, bindings):
        """
           decode_bindings(bindings) -> (encoded_oids, encoded_vals)
           
           Decode variables bindings (string), return lists or encoded
           Object IDs and their associated values (lists of strings) .
        """
        # Decode bindings
        bindings = self.decode_sequence (bindings)

        # Initialize objids and vals lists
        encoded_oids = []
        encoded_vals = []

        # Initialize index
        index = 0

        # Walk over bindings
        while index < len(bindings):
            # Get a binding
            length, size = self.decode_length (bindings[index+1:])
            binding = self.decode_sequence (bindings[index:])

            # Get the binding length
            binding_length = length + size + 1

            # Get the length of Object ID
            length, size = self.decode_length (binding[1:])
            oid_length = length + size + 1

            # Get an encoded Object ID
            encoded_oids.append(binding[:oid_length])

            # Get encoded value
            encoded_vals.append(binding[oid_length:])

            # Move to the next binding
            index = index + binding_length

        return (encoded_oids, encoded_vals)

    def decode_snmp_pdu (self, pdu):
        """
           decode_snmp_pdu(pdu) -> (type, id, err_status, err_index, bindings)
           
           Decode SNMP PDU (string), return PDU type (integer), request
           serial ID (integer), error status (integer), error index (integer)
           and variables bindings (string).

           See RFC 1157 for details.
        """
        # Decode PDU
        tag = self.decode_tag(ord(pdu[0]))
        pdu = self.decode_sequence (pdu)

        # Get request ID from PDU
        length, size = self.decode_length (pdu[1:])
        request_id = self.decode_unsigned (pdu)
        pdu = pdu[size+length+1:]

        # Get error status field
        length, size = self.decode_length (pdu[1:])
        error_status = int(self.decode_integer (pdu))
        pdu = pdu[size+length+1:]

        # Get error index field
        length, size = self.decode_length (pdu[1:])
        error_index = int(self.decode_integer (pdu))
        pdu = pdu[size+length+1:]

        return (tag, request_id, error_status, error_index, pdu)

    def decode_response (self, message, mtype='GETRESPONSE'):
        """
           decode_response(message[, type]) -> (encoded_oids, encoded_values)
           
           Decode SNMP message (string) of specified type (default is
           'GETRESPONSE'), return lists of encoded Object IDs and their
           values (lists of strings).
        """
        if not message:
            raise error.EmptyResponse('Empty SNMP message')

        # Unwrap the whole packet
        (version, community, pdu) = self.decode_response_sequence(message)

        # Check response validness
        if version != self.version:
            raise error.BadVersion('Unmatched SNMP versions: ' + str(version))
        if community != self.community:
            raise error.BadCommunity('Unmatched SNMP community names: ' \
                                     + str(community))

        (tag, request_id, error_status, error_index, bindings) = \
                         self.decode_snmp_pdu (pdu)

        # Make sure request ID's matched
        if request_id != self.request_id:
            raise error.BadRequestID ('Unmatched request/response IDs: %s vs %s'\
                                      % (request_id, self.request_id))

        # Check the PDU type if given
        if mtype and tag == self.encode_tag(mtype):
            raise error.BadPDUType('Unexpected PDU type: ' + str(mtype))

        # Check error status
        if error_status > 0:
            # Remote failed to process our request
            raise error.SNMPError(error_status, error_index)

        # Decode variables bindings
        (encoded_oids, encoded_values) = self.decode_bindings(bindings)

        # Return encoded OID's and values
        return (encoded_oids, encoded_values)

    def decode_snmp_trap_pdu (self, pdu):
        """
           decode_snmp_trap_pdu (pdu) -> (enterprise, addr, generic,
                                          specific, timeticks, bindings)
                                 
           Decode SNMP trap PDU (string) to enterpise Object-ID (list of
           integer sub-IDs), agent IP address (string), generic trap type
           (integer), specific trap type (integer), timeticks (integer) and
           variable bindings (string).

           See RFC-1157 for details.
        """
        # Decode PDU
        tag = self.decode_tag(ord(pdu[0]))
        pdu = self.decode_sequence (pdu)

        # Get enterprise from PDU
        length, size = self.decode_length (pdu[1:])
        enterprise = self.decode_oid (pdu)
        pdu = pdu[size+length+1:]

        # Get agent address from PDU
        length, size = self.decode_length (pdu[1:])
        addr = self.decode_ipaddr (pdu)
        pdu = pdu[size+length+1:]

        # Get generic trap from PDU
        length, size = self.decode_length (pdu[1:])
        generic = self.decode_integer (pdu)
        pdu = pdu[size+length+1:]

        # Get specific trap from PDU
        length, size = self.decode_length (pdu[1:])
        specific = self.decode_integer (pdu)
        pdu = pdu[size+length+1:]

        # Get uptime from PDU
        length, size = self.decode_length (pdu[1:])
        timeticks = self.decode_timeticks (pdu)
        pdu = pdu[size+length+1:]

        return (tag, enterprise, addr, generic, specific, timeticks, pdu)

    def decode_trap (self, message):
        """
           decode_trap(message) -> (enterprise, addr, generic, specific,
                                    timeticks, encoded_oids, encoded_values)
                                 
           Decode SNMP message (string), return a tuple of enterpise
           Object-ID (list of integer sub-IDs), agent IP address (string),
           generic trap type (integer), specific trap type (integer),
           timeticks (integer) along with lists of encoded Object IDs and
           their values (lists of strings).

           See RFC-1157 for details.
        """
        if not message:
            raise error.EmptyResponse('Empty SNMP message')

        # Unwrap the message
        (version, community, pdu) = self.decode_response_sequence(message)

        # Check response validness
        if version != self.version:
            raise error.BadVersion('Unmatched SNMP versions: ' + str(version))
        if community != self.community:
            raise error.BadCommunity('Unmatched SNMP community names: %s vs %s'  % (community, self.community))

        (tag, enterprise, addr, generic, specific, timeticks, bindings) = \
              self.decode_snmp_trap_pdu (pdu)

        # Check the PDU type if given
#        if self.decode_tag(tag) != 'TRAPREQUEST':
#            raise error.BadPDUType('Non-trap PDU type')

        # Decode variables bindings if present
        if bindings:
            (encoded_oids, encoded_values) = self.decode_bindings(bindings)
        else:
            (encoded_oids, encoded_values) = ([], [])

        return (enterprise, addr, generic, specific, timeticks, \
                encoded_oids, encoded_values)
