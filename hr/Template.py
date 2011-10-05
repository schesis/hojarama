# -*- coding: utf-8 -*-

# hr/Template.py
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

"""Language-specific page template."""

import os
import sys

from copy import deepcopy
from glob import glob
from lxml import etree

from hojarama import (HojaramaError, log, MISSING_TEXT, NS, Persistent, pop,
                      ROOT, strip_ns, WHITESPACE)

from Config import Config
from Translations import Translations
from Index import Index

CONFIG = Config()


def _collapse(element):
    """Remove superfluous whitespace from `element`."""
    if element.text:
        element.text = WHITESPACE.sub("\n", element.text)
    if element.tail:
        element.tail = WHITESPACE.sub("\n", element.tail)


def _global_nav(lang_id, max_level, nbsp, record=None, index=None):
    """Build a branch of the navigation menu."""
    index = index or Index(lang_id)
    record = record or index[0]
    element = etree.Element("ul")
    if record.level < max_level:
        for child in (r for r in index if r.parent == record):
            li_elem = etree.Element("li")
            a_elem = etree.Element("a", href="/%s/%s" % (child.node, lang_id))
            if child.title is None:
                a_elem.text = MISSING_TEXT
            elif nbsp:
                a_elem.text = child.title.replace(" ", unichr(160))
            else:
                a_elem.text = child.title
            li_elem.append(a_elem)
            ul_elem = _global_nav(lang_id, max_level, nbsp, child, index)
            if len(ul_elem) > 0:
                li_elem.append(ul_elem)
                li_elem.set("class", "branch")
            else:
                li_elem.set("class", "leaf")
            element.append(li_elem)
    return element


class Template(Persistent):

    """Language-specific page template."""

    def __init__(self, name, lang_id):
        self.__xml_data = None
        self.name = name
        self.lang_id = lang_id
        self.path = os.path.join(ROOT, "cache", "templates", self.name,
                                 lang_id + ".xml")
        Persistent.__init__(self)

    def __repr__(self):
        return "<Template '%s/%s'>" % (self.name, self.lang_id)

    def __xml_global_nav(self, element):
        """Replace `element` with a navigation menu."""
        element.tag = "ul"
        existing_class = element.get("class")
        if existing_class is None:
            element.set("class", CONFIG.nav_class)
        else:
            element.set("class", "%s %s" % (CONFIG.nav_class, existing_class))
        max_level = pop(element, "max_level", sys.maxint)
        nbsp = pop(element, "nbsp", False)
        element[:] = _global_nav(self.lang_id, max_level, nbsp)[:]

    def __xml_translate(self, element, translations):
        """Translate the hr:translate element `element`."""
        element.tag = pop(element, "tag", "span")
        msg = "cannot translate element %s" % element.tag
        lookup = pop(element, "from")
        if lookup is None:
            log.warning("%s: has no 'from' attribute" % msg)
        else:
            try:
                element.text = translations[lookup][self.lang_id]
            except KeyError:
                log.warning("%s: no translation for %s in %s"
                            % (msg, lookup, self.lang_id))

    def __xml_translate_attrs(self, element, translations):
        """Translate hr:attr_name="lookup" attributes in `element`."""
        for attribute, lookup in element.items():
            if attribute.startswith("{%s}" % NS):
                new_attr = strip_ns(attribute)
                msg = "cannot translate attribute %s" % new_attr
                try:
                    replacement = translations[lookup][self.lang_id]
                except KeyError:
                    log.warning("%s: no translation for %s in %s"
                                % (msg, lookup, self.lang_id))
                else:
                    element.set(new_attr, replacement)
                finally:
                    del(element.attrib[attribute])

    def _build(self):
        """Build the language-specific page template from its master."""
        translations = Translations()
        master = os.path.join(ROOT, "site", "templates", self.name + ".xml")
        self.__xml_data = deepcopy(etree.ElementTree(file=master))
        for element in self.__xml_data.getiterator():
            _collapse(element)
        for tr_elem in self.__xml_data.getiterator("{%s}translate" % NS):
            self.__xml_translate(tr_elem, translations)
        tr_attr = "//*[@*[namespace-uri()='%s']]" % NS
        for tr_attr_elem in self.__xml_data.xpath(tr_attr):
            self.__xml_translate_attrs(tr_attr_elem, translations)
        for nav_elem in self.__xml_data.getiterator("{%s}global_nav" % NS):
            self.__xml_global_nav(nav_elem)

    def _read(self):
        """Read the template from an XML file."""
        self.__xml_data = etree.ElementTree(file=self.path)

    def xml(self):
        """Return an XML representation of the template."""
        return self.__xml_data

    @staticmethod
    def translations(return_type):
        """Return the set of all translations in use by any templates."""
        found = return_type()
        tr_predicate = "local-name()='translate'"
        ns_predicate = "namespace-uri()='%s'" % NS
        element_search = "//*[%s][%s]/@from" % (tr_predicate, ns_predicate)
        attribute_search = "//*/@*[%s]" % ns_predicate
        for path in glob(os.path.join(ROOT, "site", "templates", "*.xml")):
            try:
                template = etree.ElementTree(file=path)
            except IOError:
                log.warning("can't read file %s" % path)
            except etree.XMLSyntaxError:
                log.warning("%s is not a valid XML file" % path)
            else:
                if return_type is set:
                    found.update(template.xpath(element_search))
                    found.update(template.xpath(attribute_search))
                elif return_type is dict:
                    filename = os.path.basename(path)
                    found[filename] = set(template.xpath(element_search))
                    found[filename].update(template.xpath(attribute_search))
                else:
                    raise HojaramaError("return_type must be <set> or <dict>")
        return found

