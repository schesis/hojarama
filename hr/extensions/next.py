# -*- coding: UTF-8 -*-

# hr/extensions/next.py
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
A link to the next page in the site.

Convert e.g. ::

    <hr:next prefix="Next: "/>

to::

    <p><em>Next:</em> <a href="/path/to/next-page/en">Next page</a></p>

Attributes
----------

================= ========= =============================================
Name              Default   Description
================= ========= =============================================
default_text      [1]_      Text for a link to an untitled page.
loop              "no"      Display a link on the last page.
loop_prefix       prefix    Prefix for a link on the last page. [2]_
loop_target       "" [3]_   Target of a link on the last page.
loop_text         [4]_      Text for a link on the last page.
prefix            None      Emphasised text before the link. [2]_
tag               "p"       Tag name of the resulting element. [5]_
unindexed         "no"      Display a link on an unindexed page.
unindexed_prefix  prefix    Prefix for a link on an unindexed page. [2]_
unindexed_target  "" [3]_   Target of a link on an unindexed page.
unindexed_text    [4]_      Text for a link on an unindexed page.
================= ========= =============================================

.. [1]  Defaults to ``MISSING_TEXT`` - "[?]" in a clean installation.

.. [2]  If any of ``prefix``, ``loop_prefix`` or ``unindexed_prefix`` end
        with a space, that space will be placed immediately after the
        resulting <em> element.

.. [3]  The root page.

.. [4]  Defaults to the title of the root page, or ``default_text`` if
        the root page is untitled.

.. [5]  Sensible choices are "p" [the default], "div" or "span".

"""

from lxml import etree

from hojarama import HojaramaError, MISSING_TEXT, pop

from Index import Index


def _details(element, node, lang_id):
    """Return appropriate prefix, target and text for `element`."""
    index = Index(lang_id)
    default_text = pop(element, "default_text", MISSING_TEXT)
    prefix = pop(element, "prefix")
    loop = pop(element, "loop", False)
    loop_prefix = pop(element, "loop_prefix", prefix)
    loop_target = pop(element, "loop_target", "")
    loop_text = pop(element, "loop_text", index[0].title or default_text)
    unindexed = pop(element, "unindexed", False)
    unindexed_prefix = pop(element, "unindexed_prefix", prefix)
    unindexed_target = pop(element, "unindexed_target", "")
    unindexed_text = pop(element, "unindexed_text",
                         index[0].title or default_text)
    if node in (r.node for r in index):
        next = index.next(node)
        if next is not None:
            return (prefix, next.node, next.title or default_text)
        elif loop:
            return (loop_prefix, loop_target, loop_text)
        else:
            raise HojaramaError("page is last in index")
    elif unindexed:
        return (unindexed_prefix, unindexed_target, unindexed_text)
    else:
        raise HojaramaError("page is unindexed")


def mutate(element, node, lang_id):
    """Transform the hr:next element `element`."""
    element.tag = pop(element, "tag", "p")
    try:
        prefix, target, text = _details(element, node, lang_id)
    except HojaramaError:
        element.getparent().remove(element)
        return
    if prefix is not None:
        em_elem = etree.Element("em")
        if prefix[-1] == " ":
            em_elem.text = prefix[:-1]
            em_elem.tail = " "
        else:
            em_elem.text = prefix
        element.append(em_elem)
    a_elem = etree.Element("a")
    if target == "":
        a_elem.set("href", "/" + lang_id)
    else:
        a_elem.set("href", "/%s/%s" % (target, lang_id))
    a_elem.text = (text)
    element.append(a_elem)

