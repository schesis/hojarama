# -*- coding: utf-8 -*-

# hr/Index.py
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

"""Site index."""

import os

from lxml import etree

from hojarama import Node, Persistent, pop, ROOT


class Index(Persistent, list):

    """Site index."""

    def __init__(self, lang_id):
        self.lang_id = lang_id
        self.path = os.path.join(ROOT, "cache", "indices", lang_id + ".xml")
        list.__init__(self)
        Persistent.__init__(self)

    def __getitem__(self, key):
        if isinstance(key, int):
            return list.__getitem__(self, key)
        else:
            for record in self:
                if record.node == key:
                    return record
            else:
                raise KeyError(key)

    def __repr__(self):
        return "<Index '%s'>" % self.lang_id

    def __build_branch(self, level, parent):
        """Build a branch of the index."""
        path = os.path.join(ROOT, "site", "pages", parent.node.path())
        try:
            branch_index = etree.ElementTree(file=os.path.join(path,
                                                               "index.xml"))
        except IOError:
            pass
        else:
            for page_id in [p.get("id") for p in branch_index.getroot()]:
                page_path = os.path.join(path, page_id, self.lang_id + ".xml")
                page = etree.ElementTree(file=page_path)
                if not pop(page.getroot(), "hidden", False):
                    if parent.node == "":
                        node = Node(page_id)
                    else:
                        node = Node("%s/%s" % (parent.node, page_id))
                    title = pop(page.getroot(), "title")
                    self.append(IndexRecord(level, node, parent, title))
                    self.__build_branch(level + 1, self[-1])

    def _build(self):
        """Build the index from scratch."""
        path = os.path.join(ROOT, "site", "pages", self.lang_id + ".xml")
        doc = etree.ElementTree(file=path)
        title = pop(doc.getroot(), "title")
        self[:] = [IndexRecord(0, Node(""), None, title)]
        self.__build_branch(1, self[0])

    def _read(self):
        """Read the index from an XML file."""
        self[:] = []
        doc = etree.ElementTree(file=self.path)
        for record in doc.getroot():
            level = int(record.get("level"))
            node = Node(record.get("node"))
            try:
                parent = self[int(record.get("parent"))]
            except TypeError:
                parent = None
            title = record.get("title")
            self.append(IndexRecord(level, node, parent, title))

    def next(self, node):
        """Return the next record in the index."""
        return self.shift(node, +1)

    def previous(self, node):
        """Return the previous record in the index."""
        return self.shift(node, -1)

    def shift(self, node, distance):
        """Return the record `distance` items away in the index."""
        try:
            return self[self.index(self[node]) + distance]
        except (KeyError, ValueError, IndexError):
            return None

    def xml(self):
        """Return an XML representation of the index."""
        index_root = etree.Element("index")
        for record in self[:]:
            page_elem = etree.Element("page", level=str(record.level),
                                      node=record.node)
            parent = record.parent
            if parent is not None:
                page_elem.set("parent", str(self.index(parent)))
            title = record.title
            if title is not None:
                page_elem.set("title", title)
            index_root.append(page_elem)
        return etree.ElementTree(index_root)


class IndexRecord(object):

    """Site index record."""

    def __init__(self, level, node, parent=None, title=None):
        self.level = level
        self.node = node
        self.parent = parent
        self.title = title

    def __repr__(self):
        return "<IndexRecord '%s'>" % self.node

