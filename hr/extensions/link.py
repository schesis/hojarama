# -*- coding: utf-8 -*-

# hr/extensions/link.py
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

"""
A <link> element.

Convert e.g. ::

    <hr:link rel="up">

to::

    <link href="/path/to/parent/en" rel="up" title="Parent page title"/>

Attributes
----------

========= ======= =======================================================
Name      Default Description
========= ======= =======================================================
default   None    Title of a link to an untitled target page. [1]_

rel       "next"  Link relationship; one of:

                  - "contents", "first", "home", "index", "start" [2]_
                  - "next"
                  - "prev", "previous" [2]_
                  - "end", "last" [2]_
                  - "up"

title     None    Link title. [3]_
========= ======= =======================================================

.. [1]  Ignored if title is set.

.. [2]  These options are equivalent.

.. [3]  Overrides any existing title of a target page.

Notes
-----

According to the XHTML specification, <link> elements must be placed
inside the <head> section of the page.

"""

from hojarama import pop

from Index import Index


def _target_page(element, node, lang_id):
    """Return the index record for the specified relation's target page."""
    index = Index(lang_id)
    relation = element.get("rel")
    if relation in ("contents", "first", "home", "index", "start"):
        return index[0]
    elif relation in ("end", "last"):
        return index[-1]
    elif relation in ("prev", "previous"):
        return index.previous(node)
    elif relation == "up":
        try:
            return index[node].parent
        except KeyError:
            return None
    else:
        element.set("rel", "next")
        return index.next(node)


def mutate(element, node, lang_id):
    """Transform the hr:link element `element`."""
    element.tag = "link"
    default = pop(element, "default")
    target = _target_page(element, node, lang_id)
    if target is None:
        element.getparent().remove(element)
        return # no link target
    if target.node == "":
        element.set("href", "/%s" % lang_id)
    else:
        element.set("href", "/%s/%s" % (target.node, lang_id))
    if element.get("title") is None:
        if target.title is not None:
            element.set("title", target.title)
        elif default is not None:
            element.set("title", default)

