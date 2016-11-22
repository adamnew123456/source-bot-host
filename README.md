# Bot Host

The bot host is a small framework for writing bots which react to events on
a Source engine server, and sends commands backs to the server in reaction.

## Writing A New Bot

The simplest bot, `log.py`, is available under `rcon/plugins`:

    def init(rcon, logger, config):
        handle = open(config['filename'], 'w')

        @logger.register
        def on_message(timestamp, message):
            if message is None:
                handle.close()
                return

            print('{}: {}'.format(timestamp, message.decode('ascii')), file=handle)

This demonstrates the skeleton structure of a plugin, and covers the basic steps:

1. The `init` function receives an open RCON connection to the Source server,
   (the class `RCON`, defined in `rcon/rcon.py`) an object which processes logs
   as they come from the log server (the class `LogSocket` in `rcon/log_parser.py`),
   and a plugin-specific configuration (as a `dict`).
2. The `init` function needs to register a handler with the logger (here done 
   via decorator syntax, but also possible via `logger.register(func)`). It 
   will receive log entries as they are collected by the log server, both
   the timestamp of the log entry (a `datetime.date`) and the contents of the
   log entry (a `bytes` object).

   When the log server shuts down (usually because of the user killing the 
   process, but also possible because a plugin shuts it down), both the 
   timestamp and the message will be `None`.
3. One thing missing from this example is that the handler function will 
   often send commands to the server via RCON. This can be done via:

       rcon.execute_command('say Hello, World!')

4. Also not shown is the use of the configuration. This will be `None` if the 
   user hasn't provided any plugin-specific configuration, but it will be a
   dictionary mapping configuration keys to configuration values.

New bots can be placed under the `plugins` directory. Note that relative
imports should be used for loading utility functions from the main module,
via something like `from .. import util`.

## Configuring the Bot Host 

The bot host service is configured via an INI-style file, with the following structure:

    [server]
    # Any of CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, or WARNING; this 
    # indicates the severity of log messages that will be written to the log
    # (Optional) The default value is WARNING
    log_level=WARNING

    # The filename to use for logging.
    # (Optional) If not provided, the server will log to the console
    log_file=/dev/null

    # A space-separated list of the plugins to load
    # (Optional) The default value is blank; no plugins are loaded
    plugins=cs_headshot log

    [rcon]
    # (REQUIRED) The host running the Source server
    host=server.hostname

    # The port that the server is running rcon on. Should not need to change this normally.
    # (OPTIONAL) The default value is 27015
    port=27015

    # (REQUIRED) The password used to connect to the server's remote rcon.
    password=my_rcon_password

    [log]
    # The port number on which to run the log processor locally.
    # (OPTIONAL) The default value is 1776.
    port=1776

    [plugin_pluginname]
    # This is the configuration for the plugin called 'pluginname'. This 
    # depends upon the plugin.

## Running The Bot Host

From this directory, the bot host can be run via:

    python3 -m rcon.service <CONFIG-FILE>

Where `<CONFIG-FILE>` is the path to the INI-style configuration file described
in the previous section.
