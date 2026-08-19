# Copyright (C) 2021 - present  Alexander Czutro <github@czutro.ch>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# For more details, see the provided licence file or
# <http://www.gnu.org/licenses>.
#
################################################################### aczutro ###

"""
A simple server to execute multiple parallel download jobs.
"""
import logging
import signal
import sys

from .client import Client
from .config import ConfigError, parseConfig
from .server import Server, ServerError


_logger = logging.getLogger(__name__)


# INFO during development, CRITICAL for releases.
_logLevel = logging.INFO


class CustomFormatter(logging.Formatter):
    """
    Logging formatter that prefixes each record with its level and logger name,
    and colours it according to its severity.
    """
    def format(self, record):
        """
        Returns the formatted log record.
        """
        message = f"{record.levelname.lower()}:{record.name}: {record.getMessage()}"
        if record.levelno == logging.INFO:
            return f"\x1b[34;4m{message}\x1b[0m"
        elif record.levelno == logging.WARNING:
            return f"\x1b[33;4m{message}\x1b[0m"
        elif record.levelno == logging.ERROR:
            return f"\x1b[31;4m{message}\x1b[0m"
        else:
            return message
        #else
    #format
#CustomFormatter


def _setUpLogging() -> None:
    """
    Sets the logging level and message format for the whole application.

    'force' is needed because czutils installs a root handler of its own as
    soon as it is imported.  Without it, that handler would survive alongside
    this one, and every record would also be run through czutils' formatter,
    which raises because czytget's records lack the fields it expects.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())

    logging.basicConfig(level=_logLevel,
                        handlers=[handler],
                        force=True,
                        )
#_setUpLogging


def _disableKeyboardInterrupt() -> None:
    """
    Makes the process ignore ^C.

    Client and server share one process, so a ^C that was meant for the client
    would tear the worker threads down with it, leaving the session
    half-finished and the per-worker cookie files unmerged.  'q' and ^D remain
    as the ways out of the shell, and both shut the server down in an orderly
    fashion.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)
#_disableKeyboardInterrupt


def main():
    """
    Main routine of the integrated czytget server/client.
    """
    _setUpLogging()
    _disableKeyboardInterrupt()

    try:
        serverConfig, clientConfig = parseConfig(".config/czytget")
        _logger.info(serverConfig)
        _logger.info(clientConfig)

        server = Server(serverConfig)
        server.start()

        client = Client(clientConfig, server)
        client.start()

        server.wait()
        client.wait()

        sys.exit(0)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except (ServerError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
    #except
#main


if __name__ == '__main__':
    sys.exit(main())
#if


### aczutro ###################################################################
