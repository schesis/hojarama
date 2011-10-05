# -*- coding: utf-8 -*-

# hr/Config.py
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

"""Configuration info."""

import logging
import os

from lxml import etree

from hojarama import HojaramaError, Persistent, ROOT, update_htaccess

FUNCS = {basestring: {"in":  lambda x: x.lower(),
                      "out": lambda x: x},

         bool:       {"in":  lambda x: x.lower() in ("y", "yes"),
                      "out": lambda x: "yes" if x else "no"},

         int:        {"in":  lambda x: int(x),
                      "out": lambda x: str(x)},

         tuple:      {"in":  lambda x: tuple(s.lower() for s in x.split(",")),
                      "out": lambda x: ",".join(x)}}

LOG_LEVELS = dict((k.lower(), v) for (k, v) in logging._levelNames.items()
                  if isinstance(k, basestring))

PREFS = {"debug_hrx":  {"default": False},

         "domain":     {"cleanup": (update_htaccess, [], {}),
                        "default": "localhost"},

         "keep_empty": {"cleanup": (Persistent.reset_cache, ["pages"], {}),
                        "default": ("area", "br", "col", "hr", "img", "input",
                                    "param", "td", "th")},

         "log":        {"convert": LOG_LEVELS,
                        "default": logging.INFO},

         "name":       {"cleanup": (Persistent.reset_cache, ["pages"], {}),
                        "default": "hr"},

         "nav_class":  {"cleanup": (Persistent.reset_cache,
                                    [("pages", "templates")], {}),
                        "default": "global_nav"}}


def _cleanup(opt):
    """Perform cleanup for the option named `opt`."""
    try:
        func, args, kwargs = PREFS[opt]["cleanup"]
    except KeyError:
        return
    else:
        return func(*args, **kwargs)


def _convert(opt, arg, direction="in"):
    """Convert between a config value and its textual representation."""
    pref = PREFS[opt]
    func = (v[direction] for (k, v) in FUNCS.items()
            if isinstance(pref["default"], k)).next()
    try:
        convert = pref["convert"]
    except KeyError:
        pass
    else:
        if direction == "in":
            try:
                arg = convert[arg.lower()]
            except KeyError:
                return pref["default"]
        else: # direction == "out" # [or func assignment would have failed]
            try:
                arg = (k for (k, v) in convert.items() if v == arg).next()
            except StopIteration:
                arg = pref["default"]
    return func(arg)


class Config(Persistent):

    """Configuration info."""

    path = os.path.join(ROOT, "site", "config.xml")

    def __init__(self):
        # Does nothing useful, but really helps the pylint score ;-)
        self.debug_hrx = None
        self.domain = None
        self.keep_empty = None
        self.log = None
        self.name = None
        self.nav_class = None
        Persistent.__init__(self)

    def _build(self):
        """Generate the configuration from default values."""
        self.__dict__.update((k, PREFS[k]["default"]) for k in PREFS)
        self.write()
        for opt in PREFS:
            _cleanup(opt)

    def _read(self):
        """Read the configuration from an XML file."""
        doc = etree.ElementTree(file=self.path)
        found = dict((e.get("id"), e.get("value")) for e in doc.getroot())
        for opt in PREFS:
            if opt in found:
                self.__dict__[opt] = _convert(opt, found[opt])
            else:
                self.__dict__[opt] = PREFS[opt]["default"]

    def apply(self, opt, val=None):
        """Set or reset the option named `opt`."""
        try:
            pref = PREFS[opt]
        except KeyError:
            raise HojaramaError("cannot set %s: no such option" % opt)
        else:
            if val is None:
                self.__dict__[opt] = pref["default"]
            else:
                self.__dict__[opt] = _convert(opt, val)
            self.write()
            _cleanup(opt)

    def defaults(self):
        """Display a formatted list of the default config values."""
        self.list(defaults=True)

    def list(self, defaults=False):
        """Display a formatted list of the config settings or defaults."""
        width = max(len(k) for k in PREFS)
        val_heading = "DEFAULT" if defaults else "VALUE"
        print "OPTION".ljust(width + 2) + val_heading
        for opt, pref in sorted(PREFS.items()):
            val = pref["default"] if defaults else self.__dict__[opt]
            print "%s  %s" % (opt.ljust(width), _convert(opt, val, "out"))

    def reset(self, opt):
        """Reset the option named `opt` to the default."""
        self.apply(opt)

    def xml(self):
        """Return an XML representation of the configuration."""
        config_root = etree.Element("config")
        for opt in sorted(PREFS):
            val = _convert(opt, self.__dict__[opt], "out")
            option_elem = etree.Element("option", id=opt, value=val)
            config_root.append(option_elem)
        return etree.ElementTree(config_root)

