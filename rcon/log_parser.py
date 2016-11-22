"""
This file contains mechanisms for parsing and acting upon the UDP logging format
used by the Source engine games.
"""
import select
import socket

from . import util

class LogSocket(util.Dispatcher):
    """
    A LogSocket sits on the network, and processes logging elements as they
    come in, sending them off to log handlers as they arrive.

    When a handler receives a log entry, it receives it in the form:

        handler(timestamp, message)

    Where timestamp is a datetime.datetime, and message is a bytestring. The
    only exception to this is when the last log entry is processed, in which
    case both are None.
    """
    READ_SIZE = 1024

    def __init__(self, ip, port):
        super().__init__()
        self.buffer = b''
        self.sock_address = (ip, port)
        self.socket = None

    def start(self):
        """
        Runs the log socket, and begins processing log entries.

        >>> log.start() # Blocking, until log.stop() is called
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.sock_address)

        pollster = select.epoll()
        pollster.register(self.socket, select.EPOLLIN)

        try:
            while True:
                pollster.poll()
                chunk, _ = self.socket.recvfrom(1024)
                self.buffer += chunk

                *messages, self.buffer = self.buffer.split(b'\0')
                for message in messages:
                    # Trim off the header, which is 6 bytes of junk plus a space.
                    # The message also has a trailing newline which we want to
                    # get rid of.
                    message = message[7:-1]
                    timestamp, message = util.parse_timestamp(message)

                    self.fire(timestamp, message)

                # Make sure that we don't process anything else, if one of the
                # callbacks killed us
                if self.socket is None:
                    break

        except KeyboardInterrupt:
            self.stop()

        self.fire(None, None)

    def stop(self):
        """
        Cleans up the socket, and stops running the server.

        >>> log.stop()
        """
        self.socket.close()
        self.socket = None
