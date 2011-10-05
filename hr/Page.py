# -*- coding: utf-8 -*-

# hr/Page.py
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

"""Page representation."""

import codecs
import os
import re

from copy import deepcopy
from lxml import etree

from hojarama import INDENT, log, NS, pop, ROOT, strip_ns, WHITESPACE

from hrio import link_file
from hrio import write_file

from Config import Config
from Content import Content
from Template import Template

CONFIG = Config()

DOCTYPE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'
           ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')


def _abort(element, msg):
    """Remove failed extension element `element` and log an error."""
    log.error("cannot apply extension %s: %s" % (strip_ns(element.tag), msg))
    element.getparent().remove(element)


def _reindent(text, indent):
    """Reindent `text`."""
    if text:
        return text.replace("\n", "\n" + indent)


class Page(object):

    """Site page."""

    root = os.path.join(ROOT, "cache", "pages")

    def __init__(self, node, lang_id):
        self.content = Content(node, lang_id)
        self.lang_id = lang_id
        self.__xhtml_data = None

    def __repr__(self):
        return "<Page '%s/%s'>" % (self.content.node, self.lang_id)

    def __create_redirect_links(self, path):
        """Create links to items in the redirection history."""
        for item in self.content.history:
            item_path = os.path.join(self.root, item, self.lang_id)
            for ext in "html", "xhtml":
                link_path = "%s.%s" % (item_path, ext)
                if not os.path.exists(link_path):
                    link_file(path, link_path)

    def __xml(self):
        """Return an XML representation of the page."""
        t_name = pop(self.content.xml.getroot(), "template", "default")
        xml_data = deepcopy(Template(t_name, self.lang_id).xml())
        self.__xml_root(xml_data.getroot())
        self.__xml_head(xml_data.find("//head"))
        self.__xml_body(xml_data.find("//body"))
        for meta_elem in xml_data.findall("//{%s}meta" % NS):
            self.__xml_meta(meta_elem)
        if self.content.node != "":
            global_nav = ("//ul[@class='%(class)s' "
                          "or starts-with(@class,'%(class)s ')]"
                          % {"class": CONFIG.nav_class})
            for global_nav_elem in xml_data.xpath(global_nav):
                self.__xml_global_nav(global_nav_elem)
        for content_elem in xml_data.getiterator("{%s}content" % NS):
            self.__xml_content(content_elem)
        for extension_elem in xml_data.getiterator("{%s}*" % NS):
            self.__xml_extensions(extension_elem)
        empty = ("//body//*[not(* "             # childless descendants of body
                 "or normalize-space() "        # without non-whitespace text
                 "or contains('|%s|', concat('|', name(), '|')))]"
                 % "|".join(CONFIG.keep_empty)) # which aren't in keep_empty
        for element in xml_data.xpath(empty):
            element.getparent().remove(element)
        return xml_data

    def __xml_body(self, element):
        """Set the id attribute on body element `element`."""
        if self.content.node == "":
            element.set("id", CONFIG.name)
        else:
            element.set("id", "_".join([CONFIG.name]
                                       + self.content.node.split("/")))

    def __xml_content(self, element):
        """Fill the template with content."""
        element.tag = pop(element, "tag", "div")
        try:
            indent = len(element.getprevious().tail.rsplit("\n")[-1]) * " "
        except AttributeError:
            indent = len(element.getparent().text.rsplit("\n")[-1]) * " "
        element.text = "\n" + indent + INDENT
        element.tail = "\n" + indent
        content = deepcopy(self.content.xml)
        for iter_elem in content.getiterator():
            iter_elem.tail = _reindent(iter_elem.tail, indent)
            iter_elem.text = _reindent(iter_elem.text, indent)
        for child_elem in content.getroot():
            element.append(child_elem)

    def __xml_extensions(self, element):
        """Transform the extension element `element`."""
        name = element.tag.rsplit("}", 1)[-1]
        try:
            module = __import__("extensions." + name, fromlist="extensions")
        except ImportError:
            _abort(element, "unable to import extension module")
        else:
            try:
                mutate = getattr(module, "mutate")
            except AttributeError:
                _abort(element, "mutate() is missing from extension module")
            else:
                try:
                    mutate(element, self.content.node, self.lang_id)
                except:
                    if CONFIG.debug_hrx:
                        raise
                    else:
                        _abort(element, "mutate() raised an exception")

    def __xml_global_nav(self, element):
        """Set class attributes for the navigation menu `element`."""
        current = ".//li[a/@href='/%s/%s']" % (self.content.node, self.lang_id)
        try:
            current_page = element.xpath(current)[0]
        except IndexError:
            pass
        else:
            current_page.attrib["class"] += " self"
            current_page[0].tag = "strong"
            del current_page[0].attrib["href"]
        ancestor = ("li[@class='branch'][a/@href='/%s/%s']"
                    % (self.content.node.split("/")[0], self.lang_id))
        try:
            ancestor_page = element.xpath(ancestor)[0]
        except IndexError:
            pass
        else:
            ancestor_page.set("class", "ancestor branch")

    def __xml_head(self, element):
        """Set the profile attribute on head element `element`."""
        profile = self.content.xml.getroot().get("profile")
        if profile is not None:
            element.set("profile", profile)

    def __xml_meta(self, element):
        """Transform the hr:meta element `element`."""
        name = pop(element, "name", "description")
        default = pop(element, "default")
        value = pop(self.content.xml.getroot(), name, default)
        if value is None:
            element.getparent().remove(element)
        else:
            element.tag = "meta"
            element.set("name", name)
            element.set("content", value)

    def __xml_root(self, element):
        """Set required attributes on root element `element`."""
        element.tag = "html"
        element.set("xmlns", "http://www.w3.org/1999/xhtml")
        element.set("lang", self.lang_id)

    def xhtml(self):
        """Return an XHTML representation of the page."""
        if self.__xhtml_data is None:
            path = os.path.join(self.root, self.content.node.path(),
                                self.lang_id) + ".xhtml"
            try:
                self.__xhtml_data = codecs.open(path, "r", "utf-8").read()
            except IOError:
                text = etree.tounicode(self.__xml())
                text = WHITESPACE.sub("\n", text)
                text = re.sub("<script ([^>]*)/>", r"<script \1></script>",
                              text)
                text = text.replace("/>", " />")
                text = text.replace(' xmlns:hr="%s"' % NS,
                                    ' xml:lang="%s"' % self.lang_id, 1)
                self.__xhtml_data = "%s\n%s" % (DOCTYPE, text)
                if self.content.cache:
                    write_file(path, self.xhtml())
                    link_file(path, path[:-5] + "html")
            finally:
                if self.content.history and self.content.cache:
                    self.__create_redirect_links(path)
        return self.__xhtml_data

