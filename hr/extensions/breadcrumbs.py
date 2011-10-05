# -*- coding: utf-8 -*-

# hr/extensions/breadcrumbs.py
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
A breadcrumb trail.

Convert e.g. ::

    <hr:breadcrumbs prefix="You are here: " root_text="Home"
      separator=" » "/>

to::

    <p><em>You are here:</em> <a href="/en">Home</a> »
      <a href="/news/en">News</a> » <a href="/news/2007/en">2007</a> »
      <strong>February</strong></p>

Attributes
----------

============= ========= =================================================
Name          Default   Description
============= ========= =================================================
current       "yes"     Include the title of the current page.

default_text  [1]_      Text of a breadcrumb whose target page is
                        untitled.

min_level     "0"       Minimum depth in the page heirarchy at which the
                        trail will be displayed.

prefix        None      Emphasised text displayed before the trail. [2]_

root_text     [3]_      Text of the first breadcrumb.

separator     " "       Text between each breadcrumb.

suffix        None      Emphasised text displayed after the trail. [4]_

tag           "p"       Tag name of the resulting element. [5]_
============= ========= =================================================

.. [1]  Defaults to ``MISSING_TEXT`` - "[?]" in a clean installation.

.. [2]  If prefix ends with a space, that space will be placed
        immediately after the resulting <em> element.

.. [3]  Defaults to the title of the root page, or ``default_text`` if
        the root page is untitled.

.. [4]  If suffix begins with a space, that space will be placed
        immediately before the resulting <em> element.

.. [5]  Sensible choices are "p" [the default], "div" or "span".

"""

from lxml import etree

from hojarama import MISSING_TEXT, pop

from Index import Index


def _add_affix(element, affix, position):
    """Add the prefix or suffix `affix` to `element`."""
    em_elem = etree.Element("em")
    if position == "prefix" and affix.endswith(" ") and len(affix) > 1:
        em_elem.text = affix[:-1]
        em_elem.tail = " "
    elif position == "suffix" and affix.startswith(" ") and len(affix) > 1:
        element[-1].tail = " "
        em_elem.text = affix[1:]
    else:
        em_elem.text = affix
    element.append(em_elem)


def _add_trail(element, record, lang_id, separator, default_text, root_text):
    """Add a breadcrumb trail to `element`."""
    crumb = record.parent
    trail = []
    while crumb:
        trail.append(crumb)
        crumb = crumb.parent
    for crumb in reversed(trail):
        a_elem = etree.Element("a")
        if crumb.node == "":
            a_elem.set("href", "/" + lang_id)
            a_elem.text = root_text or crumb.title or default_text
        else:
            a_elem.set("href", "/%s/%s" % (crumb.node, lang_id))
            a_elem.text = crumb.title or default_text
        a_elem.tail = separator
        element.append(a_elem)


def mutate(element, node, lang_id):
    """Transform the hr:breadcrumbs element `element`."""
    element.tag = pop(element, "tag", "p")
    index = Index(lang_id)
    current = pop(element, "current", True)
    default_text = pop(element, "default_text", MISSING_TEXT)
    min_level = pop(element, "min_level", 0)
    prefix = pop(element, "prefix", "")
    suffix = pop(element, "suffix", "")
    root_text = pop(element, "root_text", index[0].title)
    separator = pop(element, "separator", " ")
    try:
        record = index[node]
    except KeyError:
        element.getparent().remove(element)
        return # page is unindexed
    if record.level < min_level or record.level == 0:
        element.getparent().remove(element)
        return # page is higher than the minimum level, or is the root page
    if prefix:
        _add_affix(element, prefix, "prefix")
    _add_trail(element, record, lang_id, separator, default_text, root_text)
    if current:
        strong_elem = etree.Element("strong")
        strong_elem.text = record.title or default_text
        element.append(strong_elem)
    if suffix:
        _add_affix(element, suffix, "suffix")

