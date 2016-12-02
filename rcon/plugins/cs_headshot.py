"""
A plugin which tracks the number of headshots by each player.
"""
from collections import defaultdict

from .. import util

def init(rcon, logger, _):
    headshots = {}

    @logger.register
    def on_message(timestamp, message):
        if message is None:
            return

        if b'(headshot)' in message:
            killer_long, _, _ = list(util.get_quoted_strings(message))
            killer, _, _, _ = util.parse_player_info(killer_long)

            if killer not in headshots:
                headshots[killer] = 0

            headshots[killer] += 1
        elif b'" say "' in message and b'"!headshots' in message:
            requester_long, query = list(util.get_quoted_strings(message))
            if query.strip() == b'!headshots':
                who , _, _, _ = util.parse_player_info(requester_long)
            else:
                try:
                    who = query.split(maxsplit=1)[1]
                except ValueError:
                    rcon.execute_command('say [HEADSHOTS] Command must be either "!headshots" or "!headshots <PLAYER>" or "!headshots *"')
                    return

            if who == b'*':
                for player, count in headshots.items():
                    rcon.execute_command('say [HEADSHOTS] {} has {}'.format(player.decode('ascii'), headshots.get(player, 0)))
            else:
                rcon.execute_command('say [HEADSHOTS] {} has {}'.format(who.decode('ascii'), headshots.get(who, 0)))
