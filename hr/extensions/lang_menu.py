# -*- coding: utf-8 -*-

# hr/extensions/lang_menu.py
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
A language menu.

Convert e.g. ::

    <hr:lang_menu/>

to::

    <ul>
      <li><del>Deutsch</del></li>
      <li><a href="es">Español</a></li>
      <li><strong>English</strong><li>
      <li><a href="fr">Français</a></li>
    </ul>

Attributes
----------

=============== ======= =================================================
Name            Default Description
=============== ======= =================================================
include_hidden  "yes"   Include unavailable pages.
=============== ======= =================================================

Notes
-----

The current language is enclosed in a <strong> element. Any languages
which aren't available for the current page are either enclosed in <del>
elements or omitted, depending on the value of include_hidden. All other
languages are represented as links to the relevant page.

"""

from lxml import etree

from hojarama import pop

from Hidden import Hidden
from Languages import Languages

HIDDEN = Hidden()
LANGUAGES = Languages()


def mutate(element, node, page_lang_id):
    """Transform the hr:lang_menu element `element`."""
    element.tag = "ul"
    include_hidden = pop(element, "include_hidden", True)
    for lang_id in LANGUAGES.visible:
        li_elem = etree.Element("li")
        if node in HIDDEN[lang_id]:
            if include_hidden:
                language_elem = etree.Element("del")
            else:
                continue
        elif lang_id == page_lang_id:
            language_elem = etree.Element("strong")
        else:
            language_elem = etree.Element("a", href=lang_id, hreflang=lang_id,
                                          rel="alternate")
        language_elem.text = LANGUAGES[lang_id].name
        li_elem.append(language_elem)
        element.append(li_elem)

