# -*- coding: utf-8 -*-

# hr/Hidden.py
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

"""Catalogue of hidden pages."""

import os

from lxml import etree

from hojarama import Persistent, pop, ROOT

from Languages import Languages


class Hidden(Persistent, dict):

    """Catalogue of hidden pages."""

    path = os.path.join(ROOT, "cache", "hidden.xml")

    def __init__(self):
        dict.__init__(self)
        for lang_id in Languages().visible:
            self[lang_id] = []
        Persistent.__init__(self)

    def _build(self):
        """Build the catalogue from scratch."""
        languages = Languages()
        top = os.path.join(ROOT, "site", "pages")
        for path, _, files in os.walk(top):
            for lang_id in languages.visible:
                filename = "%s.xml" % lang_id
                if filename in files:
                    doc = etree.ElementTree(file=os.path.join(path, filename))
                    if pop(doc.getroot(), "hidden", False):
                        self[lang_id].append(path[len(top)+1:])

    def _read(self):
        """Read the catalogue from an XML file."""
        for page_elem in etree.ElementTree(file=self.path).getroot():
            self[page_elem.get("lang")].append(page_elem.get("node"))

    def xml(self):
        """Return an XML representation of the catalogue."""
        hidden_root = etree.Element("hidden")
        for lang_id in Languages().visible:
            for node in self[lang_id]:
                page_elem = etree.Element("page", lang=lang_id, node=node)
                hidden_root.append(page_elem)
        return etree.ElementTree(hidden_root)

