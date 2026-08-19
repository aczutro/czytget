# Copyright (C) 2026 - present  Alexander Czutro <github@czutro.ch>
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
Provides `Notifier`, which relays the server's unsolicited notifications to
the user.
"""
import logging
import queue
import time

from czutils.utils import czthreading
import dbus.exceptions
import notify2


_logger = logging.getLogger(__name__)


_appName = "czytget"

# The notifier polls its input queue with this timeout, so that it notices a
# stop request promptly.
_pollingInterval = 1.

# At most one desktop notification per this many seconds.  A file full of codes
# may fail hundreds of times, and that must not raise hundreds of pop-ups.
_notificationInterval = 60.

# Stock icon shown in the desktop notification.
_notificationIcon = "dialog-error"


class Notifier(czthreading.Thread):
    """
    Moves the server's notifications from the queue the server writes to, over
    to the queue the shell prints from, and raises a desktop notification, so
    that the user finds out about failures even while not looking at the
    terminal.

    The terminal itself is left alone: notifications are printed by the shell
    at its next prompt, never by this thread.
    """

    def __init__(self, source: queue.Queue, sink: queue.Queue):
        """
        :param source: the queue the server pushes notifications into.
        :param sink: the queue the shell prints from.
        """
        super().__init__("czytget-notifier")
        self._source = source
        self._sink = sink
        self._lastNotification = 0.
        self._desktopAvailable = True

        try:
            notify2.init(_appName)
        except dbus.exceptions.DBusException as e:
            _logger.warning("desktop notifications unavailable: %s", e)
            self._desktopAvailable = False
        #except
    #__init__


    def threadCode(self) -> None:
        while self.running():
            try:
                self._sink.put(self._source.get(block=True,
                                                timeout=_pollingInterval))
            except queue.Empty:
                continue
            #except

            # Take whatever else has piled up in the meantime, so that a burst
            # of failures raises one pop-up instead of one per code.
            count = 1
            while True:
                try:
                    self._sink.put(self._source.get(block=False))
                    count += 1
                except queue.Empty:
                    break
                #except
            #while

            self._popUp(count)
        #while
    #threadCode


    def _popUp(self, count: int) -> None:
        """
        Raises a desktop notification, unless the desktop back end is
        unavailable, or one has been raised very recently.
        """
        now = time.monotonic()
        if not self._desktopAvailable \
                or now - self._lastNotification < _notificationInterval:
            return
        #if
        self._lastNotification = now

        plural = "" if count == 1 else "s"
        try:
            notify2.Notification(_appName,
                                 f"{count} download{plural} failed",
                                 _notificationIcon,
                                 ).show()
        except dbus.exceptions.DBusException as e:
            _logger.warning("cannot show desktop notification: %s", e)
            self._desktopAvailable = False
        #except
    #_popUp

#Notifier


### aczutro ###################################################################
