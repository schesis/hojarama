# -*- coding: utf-8 -*-

# hr/Translations.py
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

"""Site translations."""

import os

from lxml import etree

from hojarama import HojaramaError, Persistent, ROOT

from Languages import Languages


def _defaults(term):
    """Return an entry `term` populated with default values."""
    return dict((lang_id, term) for lang_id in Languages().order)


class Translations(Persistent, dict):

    """Site translations."""

    path = os.path.join(ROOT, "site", "translations.xml")

    def _build(self):
        """Generate translations from those requested by all templates."""
        from Template import Template
        self.update((f, _defaults(f)) for f in Template.translations(set))

    def _read(self):
        """Read translations from an XML file."""
        doc = etree.ElementTree(file=self.path)
        for term in doc.getroot():
            self[term.get("id")] = dict((t.get("lang"), t.get("value"))
                                        for t in term)

    def add(self, term):
        """Add the entry `term`."""
        if term in self:
            raise HojaramaError, ("cannot add %s: already exists" % term)
        else:
            self[term] = _defaults(term)
            self.write()

    def add_language(self, lang_id):
        """Add default translations for language `lang_id` to all entries."""
        for term, defs in self.items():
            defs[lang_id] = term
        self.write()

    def apply(self, term, lang_id, value):
        """Set the translation of entry `term` for language `lang_id`."""
        msg = "cannot set translation %s of term %s" % (lang_id, term)
        if lang_id not in Languages().order:
            raise HojaramaError("%s: no such language %s" % (msg, lang_id))
        elif term not in self:
            raise HojaramaError("%s: no such term %s" % (msg, term))
        else:
            self[term][lang_id] = value
            self.write()

    def kill(self, term):
        """Remove the entry `term`."""
        from Template import Template
        msg = "cannot remove %s" % term
        in_use = Template.translations(dict)
        required = ", ".join(k for (k, v) in in_use.items() if term in v)
        if term not in self:
            raise HojaramaError("%s: no such term" % msg)
        elif required and ", " not in required:
            raise HojaramaError("%s: used by template %s" % (msg, required))
        elif required:
            raise HojaramaError("%s: used by templates %s" % (msg, required))
        else:
            del self[term]
            self.write()

    def kill_language(self, lang_id):
        """Remove translations for language `lang_id` from all entries."""
        for defs in self.values():
            del defs[lang_id]
        self.write()

    def list(self):
        """Display a formatted representation of the translations."""
        entries = []
        for term, defs in sorted(self.items()):
            body = "\n".join('%s: "%s"' % (k, v)
                             for (k, v) in sorted(defs.items()))
            entries.append("\n".join((term, "=" * len(term), body)))
        print "\n\n".join(entries)

    def xml(self):
        """Return an XML representation of the translations."""
        translations_root = etree.Element("translations")
        for term, defs in sorted(self.items()):
            term_elem = etree.Element("term", id=term)
            for key, val in sorted(defs.items()):
                trans_elem = etree.Element("translation", lang=key, value=val)
                term_elem.append(trans_elem)
            translations_root.append(term_elem)
        return etree.ElementTree(translations_root)

