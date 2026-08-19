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
Utilities shared by all czytget modules: terminal output.
"""
from typing import Any


def _makeWarning(obj: Any) -> str:
    """
    Returns the string representation of an object, with a warning prefix and in
    the warning colour.
    """
    return f"\x1b[33mwarning: {obj}\x1b[0m"
#_makeWarning


def _makeError(obj: Any) -> str:
    """
    Returns the string representation of an object, with an error prefix and in
    the error colour.
    """
    return f"\x1b[31merror: {obj}\x1b[0m"
#_makeError


class UIOutput:
    """
    Prints info, warning and error messages to the user's terminal, each in its
    own colour.

    This is the channel for output shown inside the czytget shell.  It is
    deliberately separate from logging, which carries diagnostics only.
    """

    @staticmethod
    def info(obj: Any) -> None:
        """
        Prints an informational message.
        """
        print(obj, flush=True)
    #info


    @staticmethod
    def warning(obj: Any) -> None:
        """
        Prints a warning message in the warning colour.
        """
        print(_makeWarning(obj), flush=True)
    #warning


    @staticmethod
    def error(obj: Any) -> None:
        """
        Prints an error message in the error colour.
        """
        print(_makeError(obj), flush=True)
    #error

#UIOutput


### aczutro ###################################################################
