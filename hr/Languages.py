# -*- coding: utf-8 -*-

# hr/Languages.py
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

"""Language index."""

import os

from lxml import etree

from hojarama import HojaramaError, Persistent, pop, ROOT, update_htaccess

from hrio import copy_file
from hrio import remove_file
from hrio import write_xml

from Index import Index


def _copy_page_heirarchy(from_lang, to_lang):
    """Copy the entire page heirarchy from `from_lang` to `to_lang`."""
    index = Index(from_lang)
    pages = os.path.join(ROOT, "site", "pages")
    indexed = [os.path.join(pages, p.node.path()).rstrip("/") for p in index]
    for path, _, _ in os.walk(pages):
        source = os.path.join(path, from_lang + ".xml")
        target = os.path.join(path, to_lang + ".xml")
        if copy_file(source, target) and path in indexed:
            doc = etree.ElementTree(file=target)
            doc.getroot().set("hidden", "yes")
            write_xml(target, doc)


def _reset_index_template(lang_id):
    """Remove all cached templates and indices for `lang_id`."""
    Persistent.reset_cache(os.path.join("index", lang_id + ".xml"))
    template_cache = os.path.join(ROOT, "cache", "templates")
    if os.path.isdir(template_cache):
        for target in os.listdir(template_cache):
            Persistent.reset_cache(os.path.join("templates", target,
                                   lang_id + ".xml"))


def _sane(lang_id):
    """Return the sanity status of the language identifier `lang_id`."""
    return (isinstance(lang_id, basestring)
            and len(lang_id) == 2
            and lang_id.isalpha()
            and lang_id.islower())


class Languages(Persistent, dict):

    """Language index."""

    path = os.path.join(ROOT, "site", "languages.xml")

    def __init__(self):
        self.default = None
        self.order = []
        self.visible = []
        dict.__init__(self)
        Persistent.__init__(self)

    def __delitem__(self, key):
        if key == self.default:
            raise HojaramaError("cannot remove %s: is the default" % key)
        else:
            try:
                self.order.remove(key)
            except ValueError:
                raise KeyError(key)
            else:
                if not self[key].hidden:
                    self.visible.remove(key)
                dict.__delitem__(self, key)

    def __append(self, lang_id, name, hidden=False):
        """Append language `lang_id` to the language index."""
        self[lang_id] = LanguageRecord(name, hidden)
        self.order.append(lang_id)
        if not hidden:
            self.visible.append(lang_id)

    def _build(self):
        """Build the language index from filenames in the page heirarchy."""
        found = set()
        pages = os.path.join(ROOT, "site", "pages")
        for _, _, files in os.walk(pages):
            found.update(f[:2] for f in files if f[2:] == ".xml")
        for lang_id in sorted(found):
            self.__append(lang_id, lang_id.upper())
        self.default = self.order[0]

    def _read(self):
        """Read the language index from an XML file."""
        doc = etree.ElementTree(file=self.path)
        doc_root = doc.getroot()
        self.default = doc_root.get("default")
        for lang in doc_root:
            hidden = pop(lang, "hidden", False)
            self.__append(lang.get("id"), lang.get("name"), hidden)

    def add(self, lang_id, name, hidden=True):
        """Add language `lang_id` to the language index."""
        from Translations import Translations
        msg = "cannot add %s" % lang_id
        if lang_id in self.order:
            raise HojaramaError("%s: already exists" % msg)
        elif not _sane(lang_id):
            raise HojaramaError("%s: invalid lang_id" % msg)
        else:
            self.__append(lang_id, name, hidden)
            self.write()
            _copy_page_heirarchy(self.default, lang_id)
            Translations().add_language(lang_id)
            if not hidden:
                update_htaccess()
                Persistent.reset_cache("pages")
                Persistent.reset_cache("hidden.xml")

    def hide(self, lang_id):
        """Mark language `lang_id` as hidden."""
        msg = "cannot hide %s" % lang_id
        if lang_id not in self.order:
            raise HojaramaError("%s: no such language" % msg)
        elif lang_id == self.default:
            raise HojaramaError("%s: is the default" % msg)
        elif self[lang_id].hidden:
            raise HojaramaError("%s: already hidden" % msg)
        else:
            self[lang_id].hidden = True
            self.visible.remove(lang_id)
            self.write()
            update_htaccess()
            Persistent.reset_cache("pages")
            _reset_index_template(lang_id)

    def http_pref(self):
        """Return the preferred value of `lang_id`."""
        http_accept_language = os.getenv("HTTP_ACCEPT_LANGUAGE")
        if http_accept_language is None:
            return self.default
        else:
            accept = [a.split(";") for a in http_accept_language.split(",")]
            for lang in accept:
                if len(lang) == 1:
                    lang.insert(0, "q=1.0")
                else:
                    lang.reverse()
                lang[1] = lang[1][:2]
            try:
                return max(a for a in accept if a[1] in self.visible)[1]
            except ValueError:
                return self.default

    def kill(self, lang_id):
        """remove language `lang_id` from the language index."""
        from Translations import Translations
        msg = "cannot remove %s" % lang_id
        if lang_id not in self.order:
            raise HojaramaError("%s: no such language" % msg)
        elif lang_id == self.default:
            raise HojaramaError("%s: is the default" % msg)
        else:
            pages = os.path.join(ROOT, "site", "pages")
            for path, _, _ in os.walk(pages):
                remove_file(os.path.join(path, lang_id + ".xml"))
            Translations().kill_language(lang_id)
            hidden = self[lang_id].hidden
            del self[lang_id]
            self.write()
            if not hidden:
                update_htaccess()
                Persistent.reset_cache()
                _reset_index_template(lang_id)

    def list(self):
        """Display a formatted list of the site languages."""
        print "     STATUS   ID  NAME"
        for index, lang_id in enumerate(self.order):
            if lang_id == self.default:
                status = "Default"
            elif self[lang_id].hidden:
                status = "Hidden"
            else:
                status = ""
            print "%3d  %-7s  %s  %s" % (index + 1, status, lang_id,
                                         self[lang_id].name)

    def name(self, lang_id, name):
        """Rename language `lang_id` to `name`."""
        if lang_id not in self.order:
            raise HojaramaError("cannot rename %s: no such language" % lang_id)
        else:
            self[lang_id].name = name
            self.write()
            Persistent.reset_cache("pages")

    def set_default(self, lang_id):
        """Set language `lang_id` as the default."""
        msg = "cannot set %s as default" % lang_id
        if lang_id not in self.order:
            raise HojaramaError("%s: no such language" % msg)
        elif self[lang_id].hidden:
            raise HojaramaError("%s: is hidden" % msg)
        elif lang_id == self.default:
            raise HojaramaError("%s: already the default" % msg)
        else:
            self.default = lang_id
            self.write()
            Persistent.reset_cache("pages")

    def set_order(self, order):
        """Reorder the language index."""
        if set(order) != set(self.order):
            raise HojaramaError("cannot reorder to %s: not a reordering of %s"
                                % (",".join(order), ",".join(self.order)))
        else:
            self.order = order
            self.visible = [x for x in order if not self[x].hidden]
            self.write()
            Persistent.reset_cache("pages")

    def unhide(self, lang_id):
        """Mark language `lang_id` as not hidden."""
        msg = "cannot unhide %s" % lang_id
        if lang_id not in self.order:
            raise HojaramaError("%s: no such language" % msg)
        elif not self[lang_id].hidden:
            raise HojaramaError("%s: not hidden" % msg)
        else:
            self[lang_id].hidden = False
            self.visible = [x for x in self.order if not self[x].hidden]
            self.write()
            update_htaccess()
            Persistent.reset_cache("pages")
            Persistent.reset_cache("hidden.xml")

    def xml(self):
        """Return an XML representation of the language index."""
        languages_root = etree.Element("languages", default=self.default)
        for lang_id in self.order:
            lang_elem = etree.Element("language", id=lang_id,
                                      name=self[lang_id].name)
            if self[lang_id].hidden:
                lang_elem.set("hidden", "yes")
            languages_root.append(lang_elem)
        return etree.ElementTree(languages_root)


class LanguageRecord:

    """Language index record."""

    def __init__(self, name, hidden):
        self.name = name
        self.hidden = hidden

    def __repr__(self):
        return "<LanguageRecord '%s'>" % self.name.encode("ascii",
                                                          "xmlcharrefreplace")

