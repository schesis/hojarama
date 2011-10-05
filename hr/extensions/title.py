# -*- coding: utf-8 -*-

# hr/extensions/title.py
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

r"""
The page title, with optional reformatting.

Convert e.g. ::

    <hr:title suffix="Site Name">

to::

    <h1>Page Title - Site Name</h1>

Attributes
----------

============= ================= =========================================
Name          Default           Description
============= ================= =========================================
reformat      "no"              Reformat the title using ``regex``,
                                ``replacement``, ``separator`` and
                                ``suffix``.

regex         "^([0-9]*)$"      Regular expression search pattern applied
                                to the page title. [1]_

replacement   "\{parent} (\1)"  Replacement pattern applied to the page
                                title if ``regex`` matches. [2]_

separator     " - "             Text between page title and suffix. [3]_

suffix        None              Text after the page title.

tag           "h1"              Tag name of the resulting element. [4]_
============= ================= =========================================

.. [1]  For more details on regular expressions and pattern replacement,
        see the Python documentation for the "re" module.

.. [2]  "\{parent}" is replaced by the title of the parent page. As a
        result, the default attribute values for <hr:title> transform
        numeric-only page titles as shown below [when ``reformat`` is set
        to "yes"]:

            "3" becomes "Title of parent page (3) - Title of home page"

.. [3]  Ignored if ``suffix`` is not set.

.. [4]  Sensible choices are "h1" [the default] or "title" [if used in
        the <head> element].

"""

import os
import re

from lxml import etree

from hojarama import pop, ROOT

from Index import Index


def _titles(node, lang_id):
    """Return the titles of the page and its parent."""
    try:
        record = Index(lang_id)[node]
    except KeyError: # unindexed page
        path = os.path.join(ROOT, "site", "pages", node.path(),
                            lang_id + ".xml")
        doc = etree.ElementTree(file=path)
        return pop(doc.getroot(), "title"), None
    else:
        if record.parent is None:
            return record.title, None
        else:
            return record.title, record.parent.title


def mutate(element, node, lang_id):
    """Transform the hr:title element `element`."""
    element.tag = pop(element, "tag", "h1")
    reformat = pop(element, "reformat", False)
    regex = pop(element, "regex", r"^([0-9]*)$")
    separator = pop(element, "separator", " - ")
    suffix = pop(element, "suffix")
    title, p_title = _titles(node, lang_id)
    replacement = pop(element, "replacement",
                      r"\{parent} (\1)").replace(r"\{parent}", p_title or "")
    if reformat and (title is not None) and (suffix is not None):
        element.text = re.sub(regex, replacement, title) + separator + suffix
    elif reformat and (title is not None):
        element.text = re.sub(regex, replacement, title)
    elif reformat and (suffix is not None):
        element.text = suffix
    else:
        element.text = title

