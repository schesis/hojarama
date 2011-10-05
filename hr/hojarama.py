#!/usr/bin/env python
# -*- coding: utf-8 -*-

# hr/hojarama.py
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

"""Utility functions & classes, errors, constants and logging."""

import logging
import os
import re
import sys

from hrio import remove_directory, remove_file, write_file, write_xml

INDENT = "  "
MISSING_TEXT = "[?]"
NS = "urn:hojarama:template"
ROOT = os.path.abspath(os.path.join(sys.path[0], os.pardir))
VERSION = "0.08.01"
WHITESPACE = re.compile("( *\n)+")


def _start_logger():
    """Start logging services."""
    from Config import Config
    logger = logging.getLogger("Hojarama")
    config = Config()
    logger.setLevel(config.log)
    handler = logging.StreamHandler()
    handler.setLevel(config.log)
    if "TERM" in os.environ:
        format = "%(levelname)s: %(message)s"
    else:
        format = (" %%(asctime)s  Hojarama/%s  %%(levelname)-8s "
                  " %%(filename)-16s %%(message)s ") % config.name
    datefmt = "%F %T %z"
    formatter = logging.Formatter(format, datefmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def pop(element, attr, default=None):
    """Remove, normalize and return the attribute `attr` from `element`."""
    value = element.get(attr)
    if value is None:
        return default
    else:
        del element.attrib[attr]
        if default is None or isinstance(default, basestring):
            return unicode(value)
        elif isinstance(default, bool):
            return value.lower() in ("y", "yes")
        else:
            return type(default)(value)


def strip_ns(text):
    """Return a tag name with the namespace prefix removed."""
    return text.rsplit("}", 1)[-1]


def update_htaccess():
    """Update .htaccess with the domain name, site root and languages."""
    from Config import Config
    from Languages import Languages
    config = Config()
    path = os.path.join(ROOT, ".htaccess")
    text = open(path).readlines()
    after = lambda tag: 1 + text.index("### DO NOT EDIT ### %s\n" % tag)
    updates = {"cache":  "RewriteCond %s/cache/pages%%{REQUEST_URI}.xhtml -f\n"
                         % ROOT,
               "lang":   "RewriteRule /(%s)$ - [CO=lang:$1:%s:2103840]\n"
                         % ("|".join(Languages().visible), config.domain),
               "global": "RewriteCond %s/site/global%%{REQUEST_URI} -f\n"
                         % ROOT}
    for tag in updates:
        text[after(tag)] = updates[tag]
    write_file(path, "".join(text))


class Node(str):

    """
    The location of a node in the page heirarchy.

    ``Node`` is a string representing a URL fragment, and provides one extra
    method, ``path(self)``.

    """

    # NB: Not tested in environments other than POSIX.

    pathsep = os.path.sep
    pardir = os.pardir

    if pardir == ".." and pathsep == "/":
        path = lambda self: str(self)
    elif pardir == "..":
        path = lambda self: self.replace("/", self.pathsep)
    elif pathsep == "/":
        path = lambda self: self.replace("..", self.pardir)
    else:
        path = lambda self: os.path.join(*[t.replace("..", self.pardir)
                                           for t in self.split("/")])

    path.__doc__ = """Return a platform-specific path fragment."""


class HojaramaError(Exception):

    """Something, somewhere, has gone horribly wrong ..."""


class Persistent(object):

    """
    Base class for persistent objects.

    ``Persistent`` caches objects in memory and XML files.

    When a ``Persistent`` object is instantiated, it's retrieved from
    memory if possible, or if not, from its XML file. If all else fails,
    it's built from source data.

    Subclasses must implement the ``_build(self)``, ``_read(self)`` and
    ``xml(self)`` methods, and must set ``self.path`` to the location where
    the object's XML representation is stored.

    Any method on a subclass of ``Persistent`` which modifies the object
    must call ``self.write()`` to update the cache with the changes.

    """

    path = None

    __memo = {}

    def __init__(self):
        if os.path.exists(self.path):
            if (self.path in self.__memo and self.__memo[self.path]["mtime"]
                                             >= os.stat(self.path).st_mtime):
                self.__retrieve()
            else:
                self._read()
                self.__store()
        else:
            self._build()
            self.write()

    def __retrieve(self):
        """Retrieve the object from memory."""
        item = self.__memo[self.path]
        self.__dict__.update(item["attrs"])
        for base_class in self.__class__.__bases__:
            if base_class is not Persistent:
                base_class.__init__(self, item[base_class])

    def __store(self):
        """Store the object to memory."""
        try:
            mtime = os.stat(self.path).st_mtime
        except OSError:
            #log.warning("cannot store persistent object %s: file error" % self)
            pass
        else:
            item = {"attrs": self.__dict__, "mtime": mtime}
            for base_class in self.__class__.__bases__:
                if base_class is not Persistent:
                    item[base_class] = base_class(self)
            self.__memo[self.path] = item

    def _build(self):
        """Build the object from scratch."""
        raise NotImplementedError

    def _read(self):
        """Read the object from an XML file."""
        raise NotImplementedError

    def write(self):
        """Write the object to an XML file."""
        write_xml(self.path, self.xml(), pretty=True)
        self.__store()

    def xml(self):
        """Return an XML representation of the object."""
        raise NotImplementedError

    @staticmethod
    def reset_cache(arg=None):
        """Remove `arg` from the cache, or the whole cache if `arg` is None."""
        cache_path = os.path.join(ROOT, "cache")
        if isinstance(arg, (list, tuple)):
            for item in arg:
                Persistent.reset_cache(item)
            return
        elif arg is None:
            target_path = cache_path
        else:
            target_path = os.path.normpath(os.path.join(cache_path, arg))
        if target_path.startswith(cache_path) and os.path.exists(target_path):
            if os.path.isdir(target_path):
                for path, dirs, files in os.walk(target_path, topdown=False):
                    for target in files:
                        remove_file(os.path.join(path, target))
                    for target in dirs:
                        remove_directory(os.path.join(path, target))
            else:
                remove_file(target_path)


log = _start_logger()

