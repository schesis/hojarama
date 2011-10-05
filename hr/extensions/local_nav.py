# -*- coding: utf-8 -*-

# hr/extensions/local_nav.py
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
A list of links to children or siblings of the current page.

Convert e.g. ::

    <hr:local_nav min_level="1"/>

to::

    <dl>
      <dt><a href="/news/2007/en">2007</a></dt>
      <dd><a href="/news/2007/02/en">February</a></dd>
      <dd><a href="/news/2007/05/en">May</a></dd>
      <dd><strong>August</strong></dd>
      <dd><a href="/news/2007/11/en">November</a></dd>
    </dl>

Attributes
----------

===================== =========== =======================================
Name                  Default     Description
===================== =========== =======================================
min_level             "0"         The minimum depth in the page heirarchy
                                  at which the list will be displayed.

min_level_childless   "siblings"  What to display when at ``min_level``
                                  and the page has no children; one of:

                                  - "siblings"
                                  - "self"
                                  - "none"
===================== =========== =======================================

Notes
-----

The title of the current page is enclosed in a <strong> element.

If a page has children, the <dt> element contains the title of the
current page, and links to its children are contained in the subsequent
<dd> elements.

If a page doesn't have children, the <dt> element contains a link to the
parent page, and links to sibling pages are contained in the subsequent
<dd> elements, with the title of the current page in the appropriate
position.

If a page at the minimum level doesn't have children, behaviour depends
on the ``min_level_childless`` option.

"""

from lxml import etree

from hojarama import MISSING_TEXT, pop

from Index import Index


def _add_dt(element, tag, record, lang_id=""):
    """Add a dt element to the definition list `element`."""
    dt_elem = etree.Element("dt")
    item_elem = etree.Element(tag)
    if record.title is not None:
        item_elem.text = record.title
    if tag == "a":
        item_elem.set("href", "/%s/%s" % (record.node, lang_id))
    dt_elem.append(item_elem)
    element.append(dt_elem)


def _populate(element, items, lang_id, record=None):
    """Populate the definition list `element`."""
    for item in items:
        dd_elem = etree.Element("dd")
        if item == record:
            item_elem = etree.Element("strong")
        else:
            item_elem = etree.Element("a")
            item_elem.set("href", "/%s/%s" % (item.node, lang_id))
        item_elem.text = item.title or MISSING_TEXT
        dd_elem.append(item_elem)
        element.append(dd_elem)


def mutate(element, node, lang_id):
    """Transform the hr:local_nav element `element`."""
    element.tag = "dl"
    min_level = pop(element, "min_level", 0)
    min_level_childless = pop(element, "min_level_childless")
    index = Index(lang_id)
    try:
        record = index[node]
    except KeyError:
        element.getparent().remove(element)
        return # page is unindexed
    if record.level >= min_level:
        children = [r for r in index if r.parent == record]
        if children:
            _add_dt(element, "strong", record)
            _populate(element, children, lang_id)
        elif record.level == min_level and min_level_childless == "self":
            _add_dt(element, "strong", record)
        elif record.level == min_level and min_level_childless == "none":
            element.getparent().remove(element)
        else:
            _add_dt(element, "a", record.parent, lang_id)
            siblings = [r for r in index if r.parent == record.parent]
            _populate(element, siblings, lang_id, record)

