"""
Various utilities used for different purposes.
"""
import datetime

class Dispatcher:
    """
    A generic event dispatcher for broadcasting messages to functions.
    """
    def __init__(self):
        self.handlers = set()
        self.to_remove = set()
        self.is_running_handlers = False

    def register(self, handler):
        """
        Registers a new function to be called when a message arrives, returning
        the function that was registered.

        >>> @dispatch.register
        ... def handler():
        ...     pass
        ...
        >>> other_handler = lambda: ...
        >>> dispatch.register(other_handler)
        """
        self.handlers.add(handler)
        return handler

    def unregister(self, handler):
        """
        Removes a handler so that it doesn't receive future messages.

        >>> dispatch.unregister(handler)
        """
        if not self.is_running_handlers:
            self.handlers.remove(handler)
        else:
            self.to_remove.add(handler)

        return handler

    def fire(self, *args, **kwargs):
        """
        Invokes all the handlers with the given arguments and keyword arguments.

        >>> dispatch.fire(1, 2, 3, a=4, b=5)
        """
        self.is_running_handlers = True
        for handler in self.handlers:
            handler(*args, **kwargs)

        self.is_running_handlers = False

        self.handlers -= self.to_remove
        self.to_remove = set()

def parse_timestamp(buffer):
    """
    Parses the timestamp of the message, returning both the timestamp as well as
    the rest of the message.

    >>> timestamp, rest_of_buffer = parse_timestamp(b'2016/11/04 15:24:09: Blah blah')
    >>> assert timestamp == datetime.datetime(2016, 11, 04, 15, 24, 9)
    >>> assert rest_of_buffer == b'Blah blah'
    """
    int_buffer = []
    month, day, year, hour, minute, second = None, None, None, None, None, None
    for idx, char in enumerate(buffer):
        if char == ord(b'/'):
            if month is None:
                month = int(bytes(int_buffer))
                int_buffer = []
            elif day is None:
                day = int(bytes(int_buffer))
                int_buffer = []
        elif char == ord(b' '):
            if year is None:
                year = int(bytes(int_buffer))
                int_buffer = []
        elif char == ord(b':'):
            if hour is None:
                hour = int(bytes(int_buffer))
                int_buffer = []
            elif minute is None:
                minute = int(bytes(int_buffer))
                int_buffer = []
            elif second is None:
                second = int(bytes(int_buffer))
                # Don't bother clearing the buffer, since this is the last 
                # entry in the string
                break
        elif char in b'0123456789':
            int_buffer.append(char)

    timestamp = datetime.datetime(year, month, day, hour, minute, second)
    
    # The offset here accounts for the colon at the beginning
    buffer = buffer[idx + 2:]

    return timestamp, buffer

def parse_player_info(player_blob):
    """
    Parses out the full information on a player, returning a tuple:

        (name, player_id, user_id, team)

    Where:

      - 'name' is the player's screen name, as a byte string
      - 'player_id' is an integer assigned to that player on the server
      - 'user_id' is either a bytestring of the form '[U:...:...]' indicating a
        Steam user (i.e. a human player) or 'BOT' indicating a bot
      - 'team' can be a bytestring which is either '', 'Unassigned', 'TERRORIST' or 'CT'

    >>> parse_player_info(b'bot name<1><BOT><CT>')
    (b'bot name', b'1', b'BOT', b'CT')
    """
    # We're parsing this out of 'PLAYER NAME<PLAYER_ID><USER_ID><TEAM>', for reference
    player_blob = player_blob.strip(b'>')
    player_name_with_id, user_id, team = player_blob.split(b'><')
    player_name, player_id = player_name_with_id.split(b'<')

    return player_name, player_id, user_id, team

def get_quoted_strings(message):
    """
    A generator that provides all the quoted strings in the message.

    >>> results = get_quoted_strings(b'"Quoted" not quoted "quoted again"')
    >>> next(results)
    b'Quoted'
    >>> next(results) # Next entry would raise StopIteration
    b'quoted again'
    """
    buffer = []
    quoted = False
    for char in message:
        if char == ord(b'"'):
            quoted = not quoted

            if not quoted and buffer:
                yield bytes(buffer)
                buffer = []
        elif quoted:
            buffer.append(char)
