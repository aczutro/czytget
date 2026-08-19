# Copyright (C) 2022 - present  Alexander Czutro <github@czutro.ch>
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
interface to yt downloading library
"""
import contextlib
import io
import logging

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from czutils.utils import czcode


_logger = logging.getLogger(__name__)


# The logger handed to yt_dlp.  It discards everything: yt_dlp also raises a
# YoutubeDLError carrying the very same text, and that is what czytget reports.
# Without this, every failure would be reported twice.
_ytdlLogger = logging.getLogger("yt_dlp")
_ytdlLogger.addHandler(logging.NullHandler())
_ytdlLogger.propagate = False


@czcode.autoStr
class YTConfig:
    """
    Configuration passed to YTConnector:

    - cookies: path to the cookies file.
    - descriptions: if True, download descriptions.
    """

    def __init__(self):
        self.cookies = ""
        self.descriptions = True
    #__init__

#YTConfig


class YTConnector:
    """
    Interface to yt downloading library (currently yt_dlp).

    It needs to be instantiated in a 'with' statement in order to ensure that
    the cookie file is written correctly on exit.  Alternatively, call close()
    to force the closing of the back-end library (and thus the writing of the
    cookie file).
    """

    def __init__(self, config: YTConfig):
        ydlOptions = { "quiet": True,
                       "no_warnings": True,
                       "no_color": True,
                       "restrictfilenames": True,
                       "windowsfilenames": True,
                       "writedescription": config.descriptions,
                       "logger": _ytdlLogger,
                       "logtostderr": True,
                       "cookiefile": config.cookies,
                       "updatetime": False }
        self._ydl = yt_dlp.YoutubeDL(ydlOptions)
    #__init__


    def __del__(self):
        self.close()
    #__del__


    def __enter__(self):
        return self
    #__enter__


    def __exit__(self, *args):
        self.close()
    #__exit__


    def close(self) -> None:
        """
        Closes the downloader, in particular forcing it to write the
        cookie file.  Not necessary if the YTConnector object is instantiated
        in a 'with' statement.

        DO NOT use download(...) after this.
        """
        if self._ydl is not None:
            try:
                self._ydl.close()
            except YoutubeDLError as e:
                # Raised, for instance, when the cookie file cannot be parsed.
                # There is nothing left to salvage at this point, and close()
                # is also called from __del__, where an exception would escape
                # into the interpreter's unraisable hook instead of anywhere
                # this program could handle it.
                _logger.error("yt_dlp failed to close cleanly: %s", e)
            #except
        #if
        self._ydl = None
    #close


    def download(self, ytCode: str) -> tuple[bool, str]:
        """
        Downloads a YT code.
        :param ytCode: a valid YT code (individual video)
        :return: If successful, [ True, "" ].
                 Else, [ False, <error description> ].
        """
        try:
            exitCode = self._ydl.download([ytCode])
            if exitCode == 0:
                _logger.info("yt_dlp successfully downloaded %s", ytCode)
                return True, ""
            else:
                _logger.warning("yt_dlp failed to download %s", ytCode)
                return False, "unknown yt_dlp failure"
            #else
        except YoutubeDLError as e:
            # Not logged here: the message is handed to the caller, whose job
            # it is to report it.
            return False, str(e)
        #except
    #download

#YTConnector


def _filter(lines: list):
    """
    Returns all yt codes contained in 'lines'.

    This greps for "Available formats for" to single out lines of the form
    "[info] Available formats for g2Tm7WZ1jPs:".
    Then extracts the code (the last word minus the colon).
    """
    for line in lines:
        if "Available formats for" in line:
            yield line.split()[-1][:-1]
        #if
    #for
#_filter


def getYTList(ytCode: str, cookies: str) -> tuple[set | None, str]:
    """
    Treats 'ytCode' like a playlist and extract the codes of all individual
    videos.  Returns the codes as a set.

    :returns: If successful, returns [ <code set>, "" ].
              Else, [ None, <error description> ].
    """
    ydlOptions = { "no_color": True,
                   "listformats": True,
                   "encoding": "utf-8",
                   "cookiefile": cookies
                   }

    formatInfo =io.StringIO()
    try:
        with contextlib.redirect_stdout(formatInfo):
            with yt_dlp.YoutubeDL(ydlOptions) as ytdl:
                if ytdl.download([ytCode]) != 0:
                    _logger.warning("yt_dlp failed to download %s", ytCode)
                    return None, "unknown yt_dlp failure"
                #if
            #with
        #with
    except YoutubeDLError as e:
        _logger.warning("yt_dlp failed to download %s: %s", ytCode, e)
        return None, str(e)
    #except

    codes = set(_filter(formatInfo.getvalue().split(sep='\n')))

    if codes:
        return codes, ""
    else:
        return None, \
               "successfully extracted list info, but list is empty"
    #else
#getYTList


def mergeCookieFiles(outputFile: str, *filenames) -> None:
    """
    Merges all cookies found in the input files and writes them to one
    single cookie file.

    :param outputFile: output file
    :param filenames: input files
    """
    with open(outputFile, "w", encoding="utf-8") as ofile:
        ofile.write("# Netscape HTTP Cookie File\n")
        for inputFile in filenames:
            with open(inputFile, "r", encoding="utf-8") as ifile:
                for line in ifile:
                    if len(line):
                        if line[0] != '#':
                            ofile.write(line)
                        #if
                    #if
                #for
            #with
        #for
    #with
    ytConfig = YTConfig()
    ytConfig.cookies = outputFile
    ytConfig.descriptions = False
    with YTConnector(ytConfig):
        pass
    #with
#mergeCookieFiles


### aczutro ###################################################################
