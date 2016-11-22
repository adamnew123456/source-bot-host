"""
The following information was found on Valve's wiki at:
http://developer.valvesoftware.com/wiki/Source_RCON_Protocol

RCON has the following high-level packet structure:

                    Offset in Bytes
    0  1  2  3  4  5  6  7  8  9 10 11   ...
    +-----------+-----------+----------+------+-----+
    |    Size   | Identifier|   Type   | Body | NUL |
    +-----------+-----------+----------+------+-----+
          4           4          4        >0     1

                    Size in Bytes

    Where 'Size' is the length of the packet, encoded as a little-endian
    32-bit signed integer, 'Identifier' is a number chosen by the client 
    (which can possibly be used to identify each packet with each response)
    also encoded as a little-endian 32-bit signed integer, 'Type' is the 
    type of the request (again, little endian 32-bit signed integer,  'Body' 
    is the content of the request, and 'NUL' is a single 0 byte.

    Note that 'Body' itself is NUL terminated, so the end of each packet
    *must* contain 2 bytes of zeroes.

There are four packet types known to RCON:
 - SERVERDATA_AUTH sends an authentication request to the server. The body must
   contain the RCON password of the server. The type field should be set to 3.
 - SERVERDATA_EXECCOMMAND sends a command to the server. The body must contain
   the command to be executed on the server. The type field should be set to 2.
 - SERVERDATA_AUTH_RESPONSE responds to a SERVERDATA_AUTH request. If the
   authentication was successful, then the identifier field will be set to the
   original, client-provided identifier - otherwise, the identifier field will
   be set to -1.
 - SERVERDATA_RESPONSE_VALUE responds to a SERVERDATA_RESPONSE_VALUE, with the
   body being set to the text of the returned command. Note that the body may
   be split. How this is handled will be described in the code.
"""
from collections import namedtuple
import random
import socket
import struct
import sys

# These components make up the 'Type' field of the packet header
SERVERDATA_AUTH = 3
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_RESPONSE_VALUE = 0

# The 'id' of a sent packet is a randomly generated integer, used for 
# identifying packets that are responses to other packets (since they'll
# share IDs). The packet itself is a bytestring.
SentPacketInfo = namedtuple('SentPacketInfo', ['id', 'packet'])

# Most fields are shared with 'SentPacketInfo' and have the same meaning. The
# 'type' field is one of the 'SERVERDATA_*' values.
ReceivedPacketInfo = namedtuple('ReceivedPacketInfo',
    ['id', 'type', 'body'])

class RCON:
    """
    Represents a running RCON connection.
    """
    def __init__(self, host, port=27015):
        self.sock = socket.socket()
        self.sock.connect((host, port))

    def _build_packet(self, packet_type, body_content):
        """
        Builds a packet which can be sent over the data socket, returning a
        'SentPacketInfo' structure.

        'packet_type' can be anything of the 'SERVERDATA_*' values, and
        'body_content' is the text of the packet's body.
        """
        # The maximum allowed value for the 'Size' field in the header is
        # 4096. Take away 10 for the overhead (explained below), and you get
        # that 4086 is the maximum body size.
        if len(body_content) > 4086:
            raise ValueError('Cannot have a body size above 4086 bytes')

        # 'Identifier' is 4 bytes, 'Type' is 4 bytes, 'NUL' is 1 byte,
        # and the body is NUL terminated, (an extra 1 byte).
        PACKET_OVERHEAD = 10

        # Avoid negative IDs, since -1 can be a special value from the server
        # when receiving SERVERDATA_AUTH_RESPONSE
        MAX_ID = (2 << 30) - 1
        packet_id = random.randint(1, MAX_ID)
        
        return SentPacketInfo(packet_id,
            (struct.pack('<i', len(body_content) + PACKET_OVERHEAD) +
             struct.pack('<i', packet_id) +
             struct.pack('<i', packet_type) + 
             bytes(body_content, 'ascii') + 
             b'\0\0'))

    def _read_packet(self):
        """
        Reads an RCON packet, while doing some basic validation to avoid
        processing invalid packets. Returns a 'ReceivedPacketInfo' structure.
        """
        # *Ensure* that we get the whole size. This is unlikely to fail (and
        # thus hit the loop), but we have to be sure.
        raw_size = self.sock.recv(4)
        if not raw_size:
            raise OSError('Connection failure')

        while len(raw_size) < 4:
            raw_size += self.sock.recv(4 - len(raw_size))

        # Decode the size - if it is >4096, then bail, since this is a corrupt
        # packet. (If its <10, then its also invalid, since the header is
        # counted).
        (size,) = struct.unpack('<i', raw_size)
        if size < 10:
            raise ValueError('{} is an invalid packet size'.format(size))
        if size > 4096:
            print('WARNING: Packet size was greater than maximum allowed by protocol',
                  file=sys.stderr)

        raw_packet = self.sock.recv(size)
        while len(raw_packet) < size:
            raw_packet += self.sock.recv(size - len(raw_packet))

        # Ensure here that the 'Type' field is valid
        TYPE_OFFSET = 4 # The type is 4 bytes after the end of the 'Size' 
                        # field

        # Extract the other fields we care about
        ID_OFFSET = 0 # The ID is immediately after the end of the 'Size'
                      # field

        BODY_OFFSET = 8 # The body is 8 bytes after the end of the 'Size'
                        # field

        (packet_id,) = struct.unpack('<i', raw_packet[ID_OFFSET:ID_OFFSET + 4])

        (packet_type,) = struct.unpack('<i', 
            raw_packet[TYPE_OFFSET:TYPE_OFFSET + 4])

        # The '-2' strips off both NUL values
        packet_body = str(raw_packet[BODY_OFFSET:-2], 'ascii')

        if packet_type not in (SERVERDATA_AUTH,
                               SERVERDATA_EXECCOMMAND,
                               SERVERDATA_AUTH_RESPONSE,
                               SERVERDATA_RESPONSE_VALUE):
            raise ValueError('Packet had an invalid type')

        return ReceivedPacketInfo(packet_id, packet_type, packet_body)

    def authenticate(self, password):
        """
        Authenticates with the RCON server, using the given password. Returns
        True on a successful authentication, and False otherwise.

        >>> result = rcon.authenticate(pw)
        >>> if result:
        ...     print('Success')
        ... else:
        ...     print('Failed')
        ...
        """
        sent_packet = self._build_packet(SERVERDATA_AUTH, password)
        self.sock.send(sent_packet.packet)

        # The wiki states that the server sends two responses - the first is a
        # SERVERDATA_RESPONSE_VALUE, and the second is a     
        # SERVERDATA_AUTH_RESPONE. The first packet is used to hold the ID of
        # the response, and the second uses its ID to communicate whether or
        # not the authentication was successful.
        first_response = self._read_packet()
        second_response = self._read_packet()

        assert first_response.id == sent_packet.id
        return second_response.id != -1

    def execute_command(self, command):
        """
        Executes a string command, returning the result as a string.

        >>> rcon.execute_command('say Hello, World!')
        """
        command_packet = self._build_packet(SERVERDATA_EXECCOMMAND, command)
        self.sock.send(command_packet.packet)

        # This is a trick mentioned on the wiki - to figure out how many
        # packets the response has been split into, we send a 
        # SERVERDATA_RESPONSE_VALUE packet. The server will mirror this back
        # to us, along with a packet notifying us of the error, allowing us to
        # find the end of the command response.

        terminator_packet = self._build_packet(SERVERDATA_RESPONSE_VALUE, '')
        self.sock.send(terminator_packet.packet)

        # Read as long as the ID of the response packet matches the ID of the
        # command packet - when the ID changes, this means that we're onto
        # the termination packets
        response_bodies = []
        response_packet = self._read_packet()
        while response_packet.id == command_packet.id:
            response_bodies.append(response_packet.body)
            response_packet = self._read_packet()

        # Dump the final packets since we don't care about their content
        # (Note that one has already been taken care of, so we just have to
        # ditch the second)
        self._read_packet()

        return ''.join(response_bodies)

    def close(self):
        """
        Disconnects from an RCON session.

        >>> rcon.close()
        """
        self.sock.close()
