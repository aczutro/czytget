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

"""czytget client"""
import cmd
import queue

from .config import ClientConfig
from .messages import *
from .server import Server
from czutils.utils import czlogging, czthreading


_logger = czlogging.LoggingChannel("czytget.client",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)

def setLoggingOptions(level: int, colour=True) -> None:
    """
    Sets this module's logging level.  If not called, the logging level is
    SILENT.

    :param level: One of the following:
                  - czlogging.LoggingLevel.INFO
                  - czlogging.LoggingLevel.WARNING
                  - czlogging.LoggingLevel.ERROR
                  - czlogging.LoggingLevel.SILENT

    :param colour: If true, use colour in log headers.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.client", level, colour=colour)

#setLoggingOptions


class Client(czthreading.Thread, cmd.Cmd):

    def __init__(self, config: ClientConfig, server: Server):
        super().__init__("czytget-client")
        self._config = config
        self._server = server

    #__init__


    def threadCode(self):
        self.prompt = "\nczytget> "
        self.intro = "\nIntegrated czytget client"\
                     "\n=========================\n" \
                     "\nType 'help' or '?' to list commands."
        self.cmdloop()

    #threadCode


    def emptyline(self) -> bool:
        """
        Overwrites cmd.Cmd.emptyline so that an empty input line does nothing.
        :returns: False
        """
        return False # on true, prompt loop will end

    #emptyline


    def do_help(self, arg: str) -> bool:
        """
        Overwrites cmd.Cmd.do_help to print custom help message.
        :param arg: ignored
        :returns: False
        """
        self.stdout.write("\nCommands")
        self.stdout.write("\n========")
        self.stdout.write("\n")
        self.stdout.write("\na CODE [CODE ...]")
        self.stdout.write("\n        add YT codes to the download list")
        self.stdout.write("\n")
        self.stdout.write("\nf FILE [FILE ...]")
        self.stdout.write("\n        add all YT codes found in files to the download list")
        self.stdout.write("\n")
        self.stdout.write("\nl       list queued and processed codes")
        self.stdout.write("\n")
        self.stdout.write("\nq       terminate the server and the client")
        self.stdout.write("\n")
        return False # on true, prompt loop will end

    #do_help


    def do_a(self, args: str) -> bool:
        """
        Implements the ADD command.
        :param args: space-separated list of YT codes.
        :return: False
        """
        codes = args.split()
        if len(codes) == 0:
            self._error("add: YT code expected")
        else:
            for ytCode in codes:
                if len(ytCode) == 11:
                    _logger.info("adding code", ytCode)
                    self._server.comm(MsgAdd(ytCode))
                    self._getResponse()
                else:
                    self._error("bad YT code:", ytCode)
                #else
            #for
        #else
        return False # on true, prompt loop will end
    #do_a


    def do_f(self, args) -> bool:
        """
        Implements FILE command.
        :param args: space-separated list of file names.
        :return: False
        """
        files = args.split()
        if len(files) == 0:
            self._error("add: filename expected")
        else:
            for file in files:
                try:
                    with open(file, "r") as f:
                        codes = f.read()
                    #with
                    if len(codes) == 0:
                        self._error("file '%s' is empty" % file)
                    else:
                        _logger.info("adding file", file)
                        self.do_a(codes)
                    #else
                except FileNotFoundError:
                    self._error("file '%s' not found" % file)
                except PermissionError:
                    self._error("no read permission for file '%s'" % file)
                #except
            #for
        #else
        return False # on true, prompt loop will end
    #do_f


    def do_l(self, args) -> bool:
        """
        Implements LIST command.
        :param args: ignored
        :return: False
        """
        self._server.comm(MsgList())
        self._getResponse()
        return False # on true, prompt loop will end
    #do_l


    def do_q(self, args) -> bool:
        """
        Implements QUIT command.
        :param args: ignored
        :return: True
        """
        _logger.info("terminating server")
        self._server.comm(czthreading.QuitMessage())
        return True # on true, prompt loop will end
    #do_q


    def _error(self, *args) -> None:
        """
        Prints error message.
        """
        self.stdout.write("ERROR: ")
        self.stdout.write(' '.join(args))
        self.stdout.write("\n")
    #_error


    def _getResponse(self) -> None:
        """
        Waits for server response and prints error message in case of timeout.
        """
        try:
            self.stdout.write(
                self._server.serverResponse.get(
                    block = True,
                    timeout = self._config.responseTimeout))
            self.stdout.write("\n")
        except queue.Empty:
            self._error("server response timeout")
        #except
    #_getResponse

#Client


### aczutro ###################################################################
