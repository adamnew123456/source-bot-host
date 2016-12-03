if __name__ == '__main__':
    import configparser
    import importlib
    import logging
    import sys

    from . import rcon
    from . import log_parser
    from . import util

    config = configparser.ConfigParser()

    # These are all fairly sane values if the user doesn't provide them, though 
    # they result in a server that does nothing since it has no plugins loaded
    config['server'] = {}
    config['server']['log_level'] = 'WARNING'
    config['server']['plugins'] = ''

    config['rcon'] = {}
    config['rcon']['port'] = '27015'

    config['log'] = {}
    config['log']['port'] = '1776'

    try:
        config.read(sys.argv[1])
    except IndexError:
        print(sys.argv[0], '[CONFIG]', file=sys.stderr)
        sys.exit(1)

    log_level = getattr(logging, config['server']['log_level'])
    log_file = config['server'].get('log_file', None)

    if log_file is not None:
        logging.basicConfig(level=log_level, file=log_file)
    else:
        logging.basicConfig(level=log_level, stream=sys.stderr)

    logger = logging.getLogger('__init__')

    try:
        rcon_host = config['rcon']['host']
        rcon_port = int(config['rcon']['port'])
        rcon_password = config['rcon']['password']

        log_port = int(config['log']['port'])
    except KeyError as err:
        logger.exception(err)
        sys.exit(1)
    except ValueError as err:
        logger.exception(err)
        sys.exit(1)

    # Before we can read log messages, we have to instruct the game server to
    # send a copy of its log stream our way, which we can do via RCON
    logger.info('Connecting to server at %s:%d', rcon_host, rcon_port)
    try:
        rcon_conn = rcon.RCON(rcon_host, rcon_port)
    except OSError as err:
        logger.error('Cannot connect to server via RCON. Reason: %s', err)
        sys.exit(1)

    if not rcon_conn.authenticate(rcon_password):
        logger.error('Incorrect password')
        rcon_conn.close()

        sys.exit(1)

    our_ip, _ = rcon_conn.sock.getsockname()
    logger.info('Adding logging handle to our server at %s:%d', our_ip, log_port)

    rcon_conn.execute_command('logaddress_delall')
    rcon_conn.execute_command('logaddress_add {}:{}'.format(our_ip, log_port))
    rcon_conn.execute_command('log on')

    log_socket = log_parser.LogSocket(our_ip, log_port)

    try:
        for plugin in config['server']['plugins'].split():
            # Per-plugin configuration appears in the form:
            #
            # [plugin_death_announcer]
            # phrase=That is an ex-parrot!
            plugin_config_name = 'plugins_' + plugin

            if plugin_config_name in config:
                plugin_config = config['plugins_' + plugin]
            else:
                plugin_config = {}

            logger.info('Launching plugin %s', plugin)
            plugin_module = importlib.import_module(
                    '.plugins.' + plugin,
                    'rcon')

            plugin_module.init(rcon_conn, log_socket, plugin_config)
    except Exception as ex:
        logger.exception(ex)

    logger.info('Starting log collector')
    log_socket.start()
    logger.info('Stopped log collector')

    logger.info('Disconnecting from rcon server')
    rcon_conn.close()
    logger.info('Closed rcon connection')
