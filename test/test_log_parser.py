from datetime import datetime
import socket
from threading import Thread
import unittest

from rcon.log_parser import *

LOG_CONTENTS = b'''\xff\xff\xff\xffRL 11/20/2016 - 13:5:40: "Human<2><[U:0:12345678]><Unassigned>" joined team "CT"
\0\xff\xff\xff\xffRL 11/20/2016 - 13:5:41: "(BOT) Vladimir<3><BOT><>" connected, address "none"
\0\xff\xff\xff\xffRL 11/20/2016 - 13:5:41: "(BOT) Vladimir<3><BOT><Unassigned>" joined team "TERRORIST"
\0\xff\xff\xff\xffRL 11/20/2016 - 13:5:41: World triggered "Game_Commencing"
\0\xff\xff\xff\xffRL 11/20/2016 - 13:5:41: "(BOT) Vladimir<3><BOT><>" entered the game
\0\xff\xff\xff\xffRL 11/20/2016 - 13:5:41: "(BOT) Brad<4><BOT><>" connected, address "none"
\0\xff\xff\xff\xffRL 1/1/2000 - 12:00:00: END OF DATA
\0
'''

def sending_thread(port):
    """
    Sends LOG_CONTENTS to the log processor in chunks.
    """
    buffer = LOG_CONTENTS
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while buffer:
        head, buffer = buffer[:100], buffer[100:]
        sock.sendto(head, ('127.0.0.1', port))

    sock.close()

class LogSocketTest(unittest.TestCase):
    TEST_PORT = 15000

    def test_main(self):
        # This is a bit of a goliath test, since it tests both LogSocket's
        # dispatching capabilities, as well as that it parses things correctly
        log_proc = LogSocket('127.0.0.1', self.TEST_PORT)
        messages = []

        expected_messages = [
            (datetime(2016, 11, 20, 13, 5, 40), 
                b'"Human<2><[U:0:12345678]><Unassigned>" joined team "CT"'),

            (datetime(2016, 11, 20, 13, 5, 41), 
                b'"(BOT) Vladimir<3><BOT><>" connected, address "none"'),

            (datetime(2016, 11, 20, 13, 5, 41),
                b'"(BOT) Vladimir<3><BOT><Unassigned>" joined team "TERRORIST"'),

            (datetime(2016, 11, 20, 13, 5, 41),
                b'World triggered "Game_Commencing"'),

            (datetime(2016, 11, 20, 13, 5, 41),
                b'"(BOT) Vladimir<3><BOT><>" entered the game'),

            (datetime(2016, 11, 20, 13, 5, 41),
                b'"(BOT) Brad<4><BOT><>" connected, address "none"'),

            (datetime(2000, 1, 1, 12, 0, 0), b'END OF DATA'),
            (None, None) # Terminating marker distributed by the log collector
        ]

        @log_proc.register
        def log_message(timestamp, message):
            messages.append((timestamp, message))
            if message == b'END OF DATA':
                log_proc.stop()

        thread = Thread(target=sending_thread, args=(self.TEST_PORT,))
        thread.start()

        log_proc.start()

        thread.join()

        self.assertEqual(messages, expected_messages)

if __name__ == '__main__':
    unittest.main()
