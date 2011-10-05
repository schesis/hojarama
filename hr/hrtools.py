# -*- coding: utf-8 -*-

# hr/hrtools.py
# Copyright (c) 2007 Zero Piraeus <z@hojarama.org>
#
# This file is part of Hojarama [release 0.08.01].
#
# Hojarama is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# Hojarama is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

"""Support for command-line tools."""

import locale
import textwrap
import sys

from optparse import OptionParser

from hojarama import log, VERSION

ENCODING = locale.getpreferredencoding()

GPL_NOTICE = """[Hojarama] tools/%s Copyright (c) 2008 Zero Piraeus

This program comes with ABSOLUTELY NO WARRANTY.

This is free software, and you are welcome to redistribute it under certain
conditions. For details, see the file 'doc/licence.txt' included with this
release, or see <http://www.gnu.org/licenses/>."""

def _log_action(command, opt, arg, help_str):
    """Log the action taken."""
    if arg is None:
        log.debug("tools/%s %s # %s" % (command, opt, help_str))
    else:
        log.debug("tools/%s %s %s # %s" % (command, opt, arg, help_str))


def _callback(option, opt_str, arg, parser, command, obj, metavar, force):
    """Take an action based on the specified option."""
    _log_action(command, opt_str, arg, option.help)
    if force and not parser.values.force:
        prompt = ("Deleting %s will IRREVERSIBLY DESTROY all of its data.\n"
                  "Are you sure you want to do this?\n"
                  "Type 'yes' [in full] to continue; anything else to abort: "
                  % arg)
        if raw_input(prompt).lower() != "yes":
            sys.exit("Aborting ... ")
    if metavar is None:
        args = []
    elif "," in metavar["example"]:
        args = [[a for a in arg.decode(ENCODING).split(",")]]
    elif arg.count(":") == metavar["example"].count(":"):
        args = [a for a in arg.decode(ENCODING).split(":")]
    else:
        parser.error("option %s requires an argument of the form %s [e.g. %s]"
                     % (opt_str, metavar["name"], metavar["example"]))
    if option.dest == "set":
        method = getattr(obj, "apply")
    else:
        method = getattr(obj, option.dest)
        if not callable(method):
            method = getattr(obj, "set_" + option.dest)
    try:
        method(*args)
    except Exception, exception:
        parser.error(exception.message)


def _gpl(option, opt_str, arg, parser, command):
    """Display copyright and licensing information."""
    _log_action(command, opt_str, arg, option.help)
    try:
        print GPL_NOTICE % command
    except Exception, exception:
        parser.error(exception.message)


def run_parser(command, obj, spec, meta, confirm=None):
    """Activate the parser."""
    parser = Parser(command, obj, spec, meta, confirm)
    _, extra_args = parser.parse_args()
    if len(sys.argv) == 1 or extra_args:
        parser.print_help()


class Parser(OptionParser):

    """Option parser for command-line tools."""

    def __init__(self, command, obj, spec, meta, confirm=None):
        OptionParser.__init__(self, version="%%prog version %s" % VERSION)
        self.usage = command
        self.obj = obj
        for opt, long_opt, var, help_str in spec:
            force = (opt == confirm)
            try:
                metavar = (v for v in meta if v["name"] == var).next()
            except StopIteration:
                metavar = None
            kwargs = {"action": "callback",
                      "callback": _callback,
                      "callback_args": (command, obj, metavar, force),
                      "dest": long_opt,
                      "help": help_str}
            if force:
                self.add_option("-f", "--force",
                                action="store_true", default=False,
                                help="don't prompt to confirm --%s" % long_opt)
            if var is not None:
                kwargs["metavar"] = var
                kwargs["type"] = "string"
            self.add_option("-%s" % opt, "--%s" % long_opt, **kwargs)
            self.__update_usage(long_opt, var, force)
        self.add_option("-g", "--gpl", action="callback",
                        callback=_gpl, callback_args=(command,),
                        help="display copyright and licence information")
        self.usage = (textwrap.fill(self.usage, 79) + "\n\n"
                      + "\n".join("%(name)-5s %(help)s (e.g. %(example)s)" % v
                                  for v in meta))

    def __update_usage(self, long_opt, var, force):
        """Add an option to the usage string."""
        if (var is None) and force:
            self.usage += " [[--force] --%s]" % long_opt
        elif force:
            self.usage += " [[--force] --%s=%s]" % (long_opt, var)
        elif var is None:
            self.usage += " [--%s]" % long_opt
        else:
            self.usage += " [--%s=%s]" % (long_opt, var)

