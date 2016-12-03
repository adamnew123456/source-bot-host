"""
A plugin which tracks the number of headshots by each player.

Configuration Options
=====================

    [plugin_cs_headshots]
    # (OPTIONAL) When to reset headshots. Can be either 'map', 'round' or 'never'.
    # Defaults to 'never'.
    when_reset=never

    # (OPTIONAL) Whether to track bots or not. Can be either 'yes' or 'no'.
    # Defaults to 'no'.
    count_bots=no
"""
from collections import defaultdict

from .. import util

def init(rcon, logger, config):
    headshots = {}
    reset_policy = config.get('when_reset', 'never')
    count_bots = config.get('count_bots', 'no')

    if reset_policy not in ('never', 'round', 'map'):
        raise ValueError('when_reset option of [config_cs_headshot] must be either never, round or map')

    if count_bots not in ('yes', 'no'):
        raise ValueError('count_bots option of [config_cs_headshot] must be either yes or no')

    count_bots = count_bots == 'yes'

    @logger.register
    def on_message(timestamp, message):
        if message is None:
            return

        if b'(headshot)' in message:
            killer_long, _, _ = list(util.get_quoted_strings(message))
            killer, _, player_type, _ = util.parse_player_info(killer_long)

            if player_type == b'BOT' and not count_bots:
                return

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
        elif reset_policy == 'round' and message == b'World triggered "Round_Start"':
            headshots = {}
        elif reset_policy == 'map' and message.startswith(b'Started map'):
            headshots = {}
