# -*- coding: utf-8 -*-

# hr/Content.py
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

"""Page content."""

import os

from lxml import etree

from hojarama import HojaramaError, Node, pop, ROOT

ERROR_DIR = "error"

HTTP_ERROR = {"401": "401 Unauthorised",
              "403": "403 Forbidden",
              "404": "404 Not found",
              "500": "500 Internal server error"}

NOT_FOUND = Node(ERROR_DIR + "/404")

UNAVAILABLE = Node(ERROR_DIR + "/unavailable")


class Content(object):

    """Page content."""

    root = os.path.join(ROOT, "site", "pages")

    def __init__(self, node, lang_id):
        self.cache = True
        self.lang_id = lang_id
        self.node = node
        self.history = []
        self.xml = None
        self.__build()

    def __repr__(self):
        return "<Content '%s/%s'>" % (self.node, self.lang_id)

    def __abs_path(self):
        """Return the absolute path to an item of content."""
        raw_path = os.path.join(self.root, self.node.path())
        norm_path = os.path.normpath(raw_path)
        full_path = os.path.join(norm_path, self.lang_id + ".xml")
        if not norm_path.startswith(self.root):
            raise HojaramaError("%s is outside %s" % (raw_path, self.root))
        elif os.path.exists(full_path):
            return full_path

    def __build(self, diversion=None):
        """Read content from the filesystem, redirecting as necessary."""
        if diversion is not None:
            self.history.append(self.node)
            if diversion in self.history:
                msg = ("redirection loop: [%s] %s >> %s"
                       % (self.lang_id, " >> ".join(self.history), diversion))
                raise HojaramaError(msg)
            else:
                self.node = diversion
        path = self.__abs_path()
        if path is None and diversion == NOT_FOUND:
            raise HojaramaError("cannot find error page %s" % NOT_FOUND)
        elif path is None:
            self.cache = False
            self.__build(NOT_FOUND)
        else:
            self.xml = etree.ElementTree(file=path)
            hidden = pop(self.xml.getroot(), "hidden", False)
            redirect = pop(self.xml.getroot(), "redirect")
            self.cache = self.cache and pop(self.xml.getroot(), "cache", True)
            if hidden:
                self.cache = False
                self.__build(UNAVAILABLE)
            elif redirect is not None:
                self.__build(Node(redirect))

    def status(self):
        """Return a HTTP status message."""
        terms = self.node.split("/")
        if len(terms) == 2 and terms[0] == ERROR_DIR:
            return HTTP_ERROR.get(terms[1], "200 OK")
        else:
            return "200 OK"

