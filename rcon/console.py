"""
A standalone RCON client.

Run via:

    python3 -m rcon.console host:port
"""
from .. import rcon

import readline
import sys

def complete_metacommands(text, state):
    """
    readline autocompletion function for metacommands: .disconnect and .quit
    """
    matches = []
    if '.disconnect'.startswith(text):
        matches.append('.disconnect')
    if '.help'.startswith(text):
        matches.append('.help')

    if not matches:
        return None
    elif state < len(matches):
        return matches[state]
    else:
        return matches

def main():
    try:
        if ':' in sys.argv[1]:
            hostname, port = sys.argv[1].split(':')
            conn = rcon.RCON(hostname, int(port))
        else:
            hostname = sys.argv[1]
            conn = rcon.RCON(hostname)

        password = getpass.getpass('Password: ')

        if not conn.authenticate(password):
            print('Could not connect - password not accepted', file=sys.stderr)
            return 1

        readline.set_completer(complete_metacommands)
        readline.parse_and_bind('tab: complete')
        while True:
            command = input('> ')
            if command == '.disconnect':
                conn.disconnect()
                return 0
            elif command == '.help':
                print('.help - Print this page')
                print('.disconnect - Exit this session')
            else:
                result = conn.execute_command(command)
                print(result, end='')

    except OSError:
        print('Could not connect to RCON on', sys.argv[1], file=sys.stderr)
    except IndexError:
        print(sys.argv[0], 'HOSTNAME[:PORT]')
    except (KeyboardInterrupt, EOFError):
        conn.close()
        return 1

if __name__ == '__main__':
    import getpass
    import sys
    sys.exit(main())
