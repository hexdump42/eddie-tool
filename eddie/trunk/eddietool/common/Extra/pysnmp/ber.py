"""
   Basic Encoding Rules (BER) for ASN.1 data types.

   Written by Ilya Etingof <ilya@glas.net>, 1999, 2000, 2001

   This code is partially derived from Simon Leinen's <simon@switch.ch>
   BER Perl module.
"""
import string

# Import package components
import objid
import error

# Flags for BER tags
FLAGS = { 
    'UNIVERSAL': 0x00,
    'APPLICATION' : 0x40,
    'CONTEXT' : 0x80,
    'PRIVATE' : 0xC0,
    # Extended tags
    'PRIMITIVE': 0x00,
    'CONSTRUCTOR' : 0x20
}

# Universal BER tags
TAGS = {
    'BOOLEAN' : 0x00,
    'INTEGER' : 0x02,
    'BITSTRING' : 0x03,
    'OCTETSTRING' : 0x04,
    'NULL' : 0x05,
    'OBJID' : 0x06,
    'SEQUENCE' : 0x10,
    'SET' : 0x11,
    'UPTIME' : 0x43,
# SNMP specific tags
    'IPADDRESS' : 0x00 | FLAGS['APPLICATION'],
    'COUNTER32' : 0x01 | FLAGS['APPLICATION'],
    'GAUGE32' : 0x02 | FLAGS['APPLICATION'],
    'TIMETICKS' : 0x03 | FLAGS['APPLICATION'],
    'OPAQUE' : 0x04 | FLAGS['APPLICATION'],
    'NSAPADDRESS' : 0x05 | FLAGS['APPLICATION'],
    'COUNTER64' : 0x06 | FLAGS['APPLICATION'],
    'UNSIGNED32' : 0x07 | FLAGS['APPLICATION'],
    'TAGGEDSEQUENCE' : 0x10 | FLAGS['CONSTRUCTOR'],
# SNMP PDU specifics
    'GETREQUEST' : 0x00 | FLAGS['CONTEXT'] | FLAGS['CONSTRUCTOR'],
    'GETNEXTREQUEST' : 0x01 | FLAGS['CONTEXT'] | FLAGS['CONSTRUCTOR'],
    'GETRESPONSE' : 0x02 | FLAGS['CONTEXT'] | FLAGS['CONSTRUCTOR'],
    'SETREQUEST' : 0x03 | FLAGS['CONTEXT'] | FLAGS['CONSTRUCTOR'],
    'TRAPREQUEST' : 0x04 | FLAGS['CONTEXT'] | FLAGS['CONSTRUCTOR']
}

# Generic trap types (see RFC-1157)
TRAPS = {
    'COLDSTART': 0x00,
    'WARMSTART': 0x01,
    'LINKDOWN': 0x02,
    'LINKUP': 0x03,
    'AUTHENTICATIONFAILURE': 0x04,
    'EGPNEIGHBORLOSS': 0x05,
    'ENTERPRISESPECIFIC': 0x06
}

class ber (objid.objid):
    """BER encoders & decoders for a SNMP subset of ASN.1 data types
    """
    #
    # BER HEADER ENCODERS / DECODERS
    #

    def encode_tag (self, name):
        """
           encode_tag(name) -> octet stream
           
           Encode ASN.1 data item (specified by name) into its numeric
           representation.
        """
        # Lookup the tag ID by name
        if TAGS.has_key(name):
            return '%c' % TAGS[name]
        raise error.UnknownTag(name)

    def encode_length (self, length):
        """
           encode_length(length) -> octet string
           
           Encode ASN.1 data item length (integer) into octet stream
           representation.
        """
        # If given length fits one byte
        if length < 0x80:
            # Pack it into one octet
            return '%c' % length
        # One extra byte required
        elif length < 0xFF:
            # Pack it into two octets
            return '%c%c' % (0x81, length)
        # Two extra bytes required
        elif length < 0xFFFF:
            # Pack it into three octets
            return '%c%c%c' % (0x82, \
                (length >> 8) & 0xFF, \
                length & 0xFF)
        # Three extra bytes required
        elif length < 0xFFFFFF:
            # Pack it into three octets
            return '%c%c%c%c' % (0x83, \
                (length >> 16) & 0xFF, \
                (length >> 8) & 0xFF, \
                length & 0xFF)
        # More octets may be added
        else:
            raise error.OverFlow('Too large length: ' + str(length))

    def decode_tag (self, tag):
        """
           decode_tag(stream) -> name
           
           Decode octet stream into symbolic representation of ASN.1 data
           item type tag.
        """
        # Lookup the tag in the dictionary of known tags
        for key in TAGS.keys():
            if tag == TAGS[key]:
                return key
        raise error.UnknownTag(key)

    def decode_length (self, packet):
        """
           decode_length(stream) -> length
           
           Extract the length of data item from octet stream.
        """
        # Get the most-significant-bit
        msb = ord(packet[0]) & 0x80
        if not msb:
            return (ord(packet[0]) & 0x7F, 1)

        # Get the size if the length
        size = ord(packet[0]) & 0x7F

        # One extra byte length
        if msb and size == 1:
            return (ord(packet[1]), size+1)

        # Two extra bytes length
        elif msb and size == 2:
            result = ord(packet[1])
            result = result << 8
            return (result | ord(packet[2]), size+1)

        # Two extra bytes length
        elif msb and size == 3:
            result = ord(packet[1])
            result = result << 8
            result = result | ord(packet[2])
            result = result << 8
            return (result | ord(packet[3]), size+1)

        else:
            raise error.OverFlow ('Too many length bytes: ' + str(size))

    #
    # ASN.1 DATA TYPES ENCODERS
    #

    def encode_an_integer (self, tag, integer):
        """
           encode_an_integer(tag, integer) -> octet stream
           
           Encode tagged integer into octet stream.
        """
        # Initialize result
        result = ''

        # The 0 and -1 values need to be handled separately since
        # they are the terminating cases of the positive and negative
        # cases repectively.
        if integer == 0:
            result = '\000'
            
        elif integer == -1:
            result = '\377'
            
        elif integer < 0:
            while integer <> -1:
                integer, result = integer>>8, chr(integer & 0xff) + result
                
            if ord(result[0]) & 0x80 == 0:
                result = chr(0xff) + result
        else:
            while integer > 0:
                integer, result = integer>>8, chr(integer & 0xff) + result
                
            if (ord(result[0]) & 0x80 <> 0):
                result=chr(0x00) + result

        return self.encode_tag(tag) + \
               self.encode_length(len(result)) + \
               result

    def encode_integer (self, integer):
        """
           encode_integer(integer) -> octet stream

           Encode ASN.1 integer into octet stream.
        """
        return self.encode_an_integer ('INTEGER', integer)

    def encode_a_sequence (self, tag, sequence):
        """
           encode_a_sequence(tag, sequence) -> octet stream
           
           Encode tagged sequence (specified as string) into octet stream.
        """
        # Make a local copy and add a leading empty item
        result = sequence

        # Return encoded packet
        return self.encode_tag(tag) + \
            self.encode_length(len(result)) + \
            result

    def encode_sequence (self, sequence):
        """
           encode_sequence(sequence) -> octet stream
           
           Encode ASN.1 sequence (specified as string) into octet
           string.
        """
        return self.encode_a_sequence ('TAGGEDSEQUENCE', sequence)

    def encode_snmp_pdu_sequence (self, type, sequence):
        """
           encode_snmp_pdu_sequence(type, sequence) -> octet stream
           
           Encode SNMP PDU ASN.1 sequence (given as string) of specified
           type into octet stream.
        """
        return self.encode_a_sequence (type, sequence)

    def encode_string (self, string):
        """
           encode_string(string) -> octet stream
           
           Encode ASN.1 octet string into octet stream.
        """
        # Encode the string
        return self.encode_tag('OCTETSTRING') + \
            self.encode_length(len(string)) + \
            string

    def encode_opaque (self, octets):
        """
           encode_opaque(octets) -> octet stream
           
           Encode ASN.1 opaque into octet stream.
        """
        # Encode the opaque octets
        return self.encode_tag('OPAQUE') + \
            self.encode_length(len(octets)) + \
            string
 
    def encode_oid (self, oids):
        """
           encode_oid(oids) -> octet stream
           
           Encode ASN.1 Object ID (specified as a list of integer subIDs)
           into octet stream.
        """
        # Set up index
        index = 0

        # Skip leading empty oid
        while not oids[index]:
            index = index + 1

        # Make sure the Object ID is long enough
        if len(oids[index:]) < 2:
            raise error.BadObjectID ('Short Object ID: ' + str(oids[index:]))

        # Build the first twos
        result = oids[index] * 40
        result = result + oids[index+1]
        result = [ '%c' % int(result) ]

        # Setup index
        index = index + 2

        # Cycle through subids
        for subid in oids[index:]:
            if subid > -1 and subid < 128:
                # Optimize for the common case
                result.append('%c' % (subid & 0x7f))

            elif subid < 0 or subid > 0xFFFFFFFFL:
                raise error.BadSubObjectID('Too large Sub-Object ID: ' + str(subid))

            else:
                # Pack large Sub-Object IDs
                res = [ '%c' % (subid & 0x7f) ]
                subid = subid >> 7
                while subid > 0:
                    res.insert(0, '%c' % (0x80 | (subid & 0x7f)))
                    subid = subid >> 7

                # Convert packed Sub-Object ID to string and add packed
                # it to resulted Object ID
                result.append(string.join(res, ''))

        # Convert BER encoded Object ID to string
        result = string.join(result,'')

        return self.encode_tag('OBJID') + \
            self.encode_length(len(result)) + result

    def encode_ipaddr (self, addr):
        """
           encode_ipaddr(addr) -> octet stream
           
           Encode ASN.1 IP address (given in dotted notation as string)
           into octet stream.
        """
        # Assume address is given in dotted notation
        packed = string.split(addr, '.')

        # Make sure it is four octets length
        if len(packed) != 4:
            raise error.BadIPAddress('Malformed IP address: ' + str(addr))

        # Convert string octets into integer counterparts
        # (this is still not immune to octet overflow)
        try:
            packed = map(lambda x: string.atoi (x), packed)
        except string.atoi_error:
            raise error.BadIPAddress('Malformed IP address: ' + str(addr))
        
        # Build a result
        result = '%c%c%c%c' % (packed[0], packed[1],\
                               packed[2], packed[3])

        # Return encoded result
        return self.encode_tag('IPADDRESS') + \
            self.encode_length(len(packed)) + \
            result

    def encode_timeticks (self, timeticks):
        """
           encode_timeticks(timeticks) -> octet stream
        
           Encode ASN.1 timeticks (specified as integer) into octet stream.
        """
        return self.encode_an_integer ('TIMETICKS', timeticks)

    def encode_null(self):
        """
           encode_null() -> octet stream
           
           Encode ASN.1 NULL value into octet stream.
        """
        return self.encode_tag('NULL') + self.encode_length(0)

    #
    # ASN.1 DATA TYPES DECODERS
    #

    def decode_integer_s (self, packet, sign):
        """
           decode_integer_s(stream, sign) -> integer
           
           Decode octet stream into signed (sign != None) or unsigned ASN.1
           integer (of any length).
        """
        # Now unpack the length, stup an index on the data area
        (length, size) = self.decode_length(packet[1:])
        index = size+1

        bytes = map(ord, packet[index:index+length])

        if sign and bytes[0] & 0x80:
            result = -1 - reduce(lambda x,y: x<<8 | 0xff & ~y, bytes, 0L)
        else:
            result = reduce(lambda x,y: x<<8 | y, bytes, 0L)

        return result

    def decode_unsigned (self, packet):
        """
           decode_unsigned(stream) -> integer
           
           Decode octet stream into unsigned ASN.1 integer.
        """
        return self.decode_integer_s (packet, 0)

    def decode_integer (self, packet):
        """
           decode_integer(stream) -> integer
           
           Decode octet stream into signed ASN.1 integer.
        """
        return self.decode_integer_s (packet, 1)

    def decode_sequence (self, packet):
        """
           decode_sequence(stream) -> sequence
           
           Decode octet stream into ASN.1 sequence.
        """
        # Unpack the length
        (length, size) = self.decode_length(packet[1:])

        # Return the sequence
        return packet[size+1:size+length+1]

    def decode_string (self, packet):
        """
           decode_string(stream) -> string
           
           Decode octet stream into ASN.1 octet string.
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'OCTETSTRING':
            raise error.TypeMismatch('Non-string type: ' + str(ord(packet[0])))

        # Unpack the length
        (length, size) = self.decode_length(packet[1:])

        # Return the octets string
        return packet[size+1:size+length+1]

    def decode_opaque (self, packet):
        """
           decode_opaque(stream) -> octets

           Decode octet stream into ASN.1 opaque data item.
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'OPAQUE':
             raise error.TypeMismatch('Non-opaque type: '\
                                      + str(ord(packet[0])))
 
        # Now unpack the length
        (length, size) = self.decode_length(packet[1:])
 
        # Return the opaque string
        return packet[size+1:size+length+1]
 
    def decode_oid (self, packet):
        """
           decode_oid(stream) -> object id
           
           Decode octet stream into ASN.1 Object ID (returned as a list of
           integer subIDs).
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'OBJID':
            raise error.TypeMismatch('Non-Object ID type: '\
                                     + str(ord(packet[0])))

        # Create a list for objid
        oid = []

        # Unpack the length
        (length, size) = self.decode_length(packet[1:])

        # Set up index
        index = size+1

        # Get the first subid
        subid = ord (packet[index])
        oid.append(int(subid / 40))
        oid.append(int(subid % 40))

        # Progress index
        index = index + 1

        # Loop through the rest
        while index < length + size + 1:
            # Get a subid
            subid = ord (packet[index])

            if subid < 128:
                oid.append(subid)
                index = index + 1
            else:
                # Construct subid from a number of octets
                next = subid
                subid = 0
                while next >= 128:
                    # Collect subid
                    subid = (subid << 7) + (next & 0x7F)

                    # Take next octet
                    index = index + 1
                    next = ord (packet[index])

                    # Just for sure
                    if index > length + size:
                        return bad_integer

                # Append a subid to oid list
                subid = (subid << 7) + next
                oid.append(subid)
                index = index + 1

        # Return objid
        return oid      

    def decode_uptime (self, packet):
        """
           decode_uptime(stream) -> integer
           
           Decode octet stream into ASN.1 uptime (integer value).
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'UPTIME':
            raise error.TypeMismatch('Non-uptime type: ' + str(ord(packet[0])))

        # Decode as unsigned integer
        return self.decode_unsigned (packet)

    def decode_ipaddr (self, packet):
        """
           decode_ipaddr(stream) -> ip address

           Decode octet stream into ASN.1 IP address data item (returned
           as string in dotted numeric notation).
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'IPADDRESS':
            raise error.TypeMismatch('Non-IP address type: ' + str(ord(packet[0])))

        # Get the value from the packet
        ipaddr = self.decode_sequence (packet)

        # Check it is valid
        if len(ipaddr) != 4:
            raise error.BadIPAddress('Malformed IP address: ' + str(ipaddr))

        # Return in dotted notation
        return '%d.%d.%d.%d' % \
            (ord(ipaddr[0]), ord(ipaddr[1]), \
            ord(ipaddr[2]), ord(ipaddr[3]))

    def decode_ipaddress (self, packet):
        """Depricated compatibility stub. Use decode_ipaddr() instead.
        """
        return self.decode_ipaddr(packet)
 
    def decode_null(self, packet):
        """
           decode_null(stream) -> None
           
           Decode octet stream into ASN.1 NULL value.
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'NULL':
            raise error.TypeMismatch('Non-NULL type: ' + str(ord(packet[0])))

        # Now unpack the length
        (length, size) = self.decode_length(packet[1:])

        # Return nothing
        return ''

    def decode_timeticks (self, packet):
        """
           decode_timeticks(stream) -> timeticks
           
           Decode octet stream into ASN.1 timeticks data item (returned as
           integer).
        """
        # Make sure data types matched
        if self.decode_tag(ord(packet[0])) != 'TIMETICKS':
            raise error.TypeMismatch('Non-timeticks type: '\
                                     + str(ord(packet[0])))

        # Decode as unsigned integer
        return self.decode_unsigned (packet)

    def decode_value (self, packet):
        """
           decode_value(stream) -> value
           
           Decode octet stream into ASN.1 value (its ASN.1 type is
           determined from included BER tag). The type of returned
           value is context dependent.
        """
        # Get a tag
        tag = self.decode_tag(ord(packet[0]))

        # If it's a string
        if tag == 'OCTETSTRING':
            return self.decode_string(packet)
        elif tag == 'INTEGER':
            return self.decode_integer(packet)
        elif tag == 'UPTIME':
            return self.decode_uptime(packet)
        elif tag == 'IPADDRESS':
            return self.decode_ipaddr(packet)
        elif tag == 'TIMETICKS':
            return self.decode_timeticks(packet)
        elif tag == 'COUNTER32' or \
            tag == 'COUNTER64' or \
                tag == 'GAUGE32':
            return self.decode_unsigned(packet)
        # The following OBJID value processing has been suggested
        # by Case Van Horsen, March 14, 2000
        elif tag == 'OBJID':
            objid_n = self.decode_oid(packet)
            return self.nums2str(objid_n)
        elif tag == 'OPAQUE':
            return self.decode_opaque(packet)
        else:
            return 'Unprintable value: ' + tag

    def oid_prefix_check (self, enc_oid_1, enc_oid_2):
        """
           oid_prefix_check(encoded_oid_1, encoded_oid_2) -> boolean
           
           Compare encoded OIDs (given as lists), return non-None if
           OID1 is a prefix of OID2.

           This is intended to be used for MIB tables retrieval.
        """
        # Decode both objid's
        oid_1 = self.decode_oid(enc_oid_1)
        oid_2 = self.decode_oid(enc_oid_2)

        # Pick the shortest oid
        if len(oid_1) <= len(oid_2):
            # Get the length
            length = len(oid_1)

            # Compare oid'es
            if oid_1[:length] == oid_2[:length]:
                return not None

        # oid_1 turned to be greater than oid_2
        return None
