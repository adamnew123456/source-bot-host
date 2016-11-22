"""
A plugin which logs messages to a file.

Configuration Options
=====================

    [plugin_log]
    # (REQUIRED) The filename to use to log the log stream to
    filename=/dev/null
"""
def init(rcon, logger, config):
    handle = open(config['filename'], 'w')

    @logger.register
    def on_message(timestamp, message):
        if message is None:
            handle.close()
            return

        print('{}: {}'.format(timestamp, message.decode('ascii')), file=handle)
