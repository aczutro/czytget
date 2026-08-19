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
czytget client
"""
import cmd
import logging

from .config import ClientConfig
from .messages import *
from .notifier import Notifier
from .server import Server
from .utils import UIOutput


_ui = UIOutput()
_logger = logging.getLogger(__name__)


class Client(czthreading.Thread, cmd.Cmd):
    """
    An "integrated" czytget client that talks directly with the server via
    message passing (without additional protocol).  Meant to run in the same
    process as the server.

    Offers a basic shell (command prompt loop).
    """

    def __init__(self, config: ClientConfig, server: Server):
        super().__init__("czytget-client")
        self._config = config
        self._server = server
        self._notifications: queue.Queue[str] = queue.Queue()
        self._pending: queue.Queue[str] = queue.Queue()
        self._notifier = Notifier(self._notifications, self._pending)

    #__init__


    def threadCode(self):
        self.prompt = "\nczytget> "
        self.intro = ""
        self._server.comm(MsgSubscribe(self._notifications))
        self._notifier.start()
        _ui.info("\nIntegrated czytget client"
                 "\n========================="
                 "\n"
                 "\nType 'help' or '?' to list commands.")
        self.cmdloop()
        self._notifier.stop()

    #threadCode


    def precmd(self, line: str) -> str:
        """
        Overwrites cmd.Cmd.precmd to show the notifications that arrived while
        the user was at the prompt, before the command's own output.

        :returns: 'line', unchanged.
        """
        self._showNotifications()
        return line
    #precmd


    def postcmd(self, stop, line):
        """
        Overwrites cmd.Cmd.postcmd to show the notifications that arrived while
        the command was running.  Commands that queue many codes take a long
        time, and the first failures often arrive before they return.

        :returns: 'stop', unchanged.
        """
        self._showNotifications()
        return stop
    #postcmd


    def _showNotifications(self) -> None:
        """
        Prints and discards everything the server has notified about since the
        last time.
        """
        while True:
            try:
                _ui.error(self._pending.get(block=False))
            except queue.Empty:
                return
            #except
        #while
    #_showNotifications


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
        _ui.info("\nCommands"
                 "\n========"
                 "\n"
                 "\na CODE [CODE ...]"
                 "\n        add YT codes to the download list"
                 "\n"
                 "\nf FILE [FILE ...]"
                 "\n        add all YT codes found in files to the download list"
                 "\n"
                 "\nl       list queued, processed and finished codes"
                 "\n"
                 "\nr       retry: queue all failed codes again"
                 "\n"
                 "\nd       discard: empty the queue of failed codes"
                 "\n"
                 "\nsls     'Session LS': list previous sessions"
                 "\n"
                 "\nsld SESSION [SESSION ...]"
                 "\n        'Session LoaD': load session SESSION"
                 "\n"
                 "\nsla     'Session Load All': load all available sessions"
                 "\n"
                 "\nslf     'Session Load Finished': load all available sessions,"
                 "\n        but only finished codes"
                 "\n"
                 "\nslp     'Session Load Pending': load all available sessions,"
                 "\n        but only unfinished codes"
                 "\n"
                 "\nq       terminate the server and the client")
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
            _ui.error("add: YT code expected")
        else:
            response: queue.Queue[str] = queue.Queue(maxsize=1)
            for ytCode in codes:
                if len(ytCode) == 11:
                    _logger.info("adding code %s", ytCode)
                    self._server.comm(MsgAddCode(ytCode, response))
                    self._getResponse(response)
                elif len(ytCode) == 34:
                    _logger.info("adding code %s", ytCode)
                    self._server.comm(MsgAddList(ytCode, response))
                    self._getResponse(response, multiLine=True)
                else:
                    _ui.error(f"bad YT code: {ytCode}")
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
            _ui.error("add: filename expected")
        else:
            for file in files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        codes = f.read()
                    #with
                    if len(codes) == 0:
                        _ui.error(f"file '{file}' is empty")
                    else:
                        _logger.info("adding file %s", file)
                        self.do_a(codes)
                    #else
                except FileNotFoundError:
                    _ui.error(f"file '{file}' not found")
                except PermissionError:
                    _ui.error(f"no read permission for file '{file}'")
                #except
            #for
        #else
        return False # on true, prompt loop will end
    #do_f


    def do_r(self, _args) -> bool:
        """
        Implements RETRY command.
        :param _args: ignored
        :return: False
        """
        self._server.comm(MsgRetry())
        return False # on true, prompt loop will end
    #do_r


    def do_d(self, _args) -> bool:
        """
        Implements RETRY command.
        :param _args: ignored
        :return: False
        """
        self._server.comm(MsgDiscard())
        return False # on true, prompt loop will end
    #do_d


    def do_l(self, _args) -> bool:
        """
        Implements LIST command.
        :param _args: ignored
        :return: False
        """
        responseBuffer: queue.Queue[str] = queue.Queue()
        self._server.comm(MsgList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_l


    def do_sls(self, _args) -> bool:
        """
        Implements SESSION LS command.
        :param _args: ignored
        :return: False
        """
        responseBuffer: queue.Queue[str] = queue.Queue()
        self._server.comm(MsgSessionList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_sld(self, args) -> bool:
        """
        Implements SESSION LOAD command.
        :param args: ignored
        :return: False
        """
        sessions = args.split()
        if len(sessions) == 0:
            _ui.error("add: YT code expected")
        else:
            response: queue.Queue[str] = queue.Queue(maxsize=1)
            for session in sessions:
                _logger.info("loading session %s", session)
                self._server.comm(MsgLoadSession(session, response))
                self._getResponse(response)
            #for
        #else
        return False # on true, prompt loop will end
    #do_sld


    def do_sla(self, _args) -> bool:
        """
        Implements SESSION LOAD ALL command.
        :param _args: ignored
        :return: False
        """
        responseBuffer: queue.Queue[str] = queue.Queue()
        self._server.comm(MsgLoadAll(MsgLoadAllSelection.ALL, responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_slf(self, _args) -> bool:
        """
        Implements SESSION LOAD FINISHED command.
        :param _args: ignored
        :return: False
        """
        responseBuffer: queue.Queue[str] = queue.Queue()
        self._server.comm(MsgLoadAll(MsgLoadAllSelection.FINISHED_ONLY,
                                     responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_slf


    def do_slp(self, _args) -> bool:
        """
        Implements SESSION LOAD PENDING command.
        :param _args: ignored
        :return: False
        """
        responseBuffer: queue.Queue[str] = queue.Queue()
        self._server.comm(MsgLoadAll(MsgLoadAllSelection.PENDING_ONLY,
                                     responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_slp


    def do_EOF(self, _args) -> bool:
        """
        Reacts to ^D, which the terminal does not echo, exactly like the QUIT
        command.
        :param _args: ignored
        :return: True
        """
        _ui.info("Ctrl-D")
        return self.do_q("")
    #do_EOF


    def do_q(self, _args) -> bool:
        """
        Implements QUIT command.
        :param _args: ignored
        :return: True
        """
        _logger.info("terminating server")
        self._server.comm(czthreading.QuitMessage())
        return True # on true, prompt loop will end
    #do_q


    def _getResponse(self, responseBuffer: queue.Queue, multiLine=False) -> None:
        """
        Waits for a message (string) to be put into 'responseBuffer' and prints
        the message to the terminal.
        In case of timeout, prints an error message.
        """

        # at least one response string must arrive
        try:
            _ui.info(
                responseBuffer.get(
                    block = True,
                    timeout = self._config.longResponseTimeout \
                        if multiLine else self._config.responseTimeout
                ))
        except queue.Empty:
            _ui.error("server response timeout")
        #except

        # additional response strings are optional
        if multiLine:
            while True:
                try:
                    _ui.info(
                        responseBuffer.get(
                            block = True,
                            timeout = self._config.shortResponseTimeout))
                except queue.Empty:
                    return
                #except
            #while
        #if
    #_getResponse

#Client


### aczutro ###################################################################
