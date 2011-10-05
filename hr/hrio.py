# -*- coding: utf-8 -*-

# hr/hrio.py
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

"""Error-checking file I/O functions."""

import codecs
import logging
import os
import shutil
import sys

os.umask(0)


def on_error(msg, err=logging.WARNING):
    """Error-checking decorator for file I/O functions."""
    # NB: Not signature-preserving - this doesn't affect operation, but messes
    # with docstrings.
    def decorator(func):
        """Return an error-checking wrapper function."""
        def wrapper(*args, **kwargs):
            """Error-checking wrapper function."""
            try:
                from hojarama import log
            except ImportError:
                log = None
            try:
                func(*args, **kwargs)
            except:
                if err is None:
                    return False
                elif isinstance(err, type(logging.ERROR)):
                    try:
                        output = msg % dict(zip("123456789", args))
                    except KeyError:
                        output = ((msg + " [missing argument(s)]")
                                  % dict((n, "arg" + n) for n in "123456789"))
                    finally:
                        if log is None:
                            print >> sys.stderr, output
                        else:
                            log.log(err, output)
                        return False
                else:
                    raise
            else:
                return True
        return wrapper
    return decorator


@on_error("unable to copy file %(1)s to %(2)s")
def copy_file(source, target):
    """Copy the file `source` to `target`."""
    shutil.copyfile(source, target)


@on_error("unable to create directory %(1)s")
def create_directory(target):
    """Create a directory `target`, and its parents if necessary."""
    if not os.path.exists(target):
        os.makedirs(target)


@on_error("unable to link file %(1)s to %(2)s")
def link_file(source, target):
    """Link the file `source` to `target`, or copy it if unable to link."""
    try:
        os.symlink(source, target)
    except AttributeError:
        try:
            os.link(source, target)
        except AttributeError:
            copy_file(source, target)


@on_error("unable to remove directory %(1)s")
def remove_directory(target):
    """Remove the directory `target`."""
    os.rmdir(target)


@on_error("unable to remove file %(1)s")
def remove_file(target):
    """Remove the file `target`."""
    os.remove(target)


@on_error("unable to write file %(1)s")
def write_file(target, data):
    """Write `data` to a file `target`."""
    dirname = os.path.dirname(target)
    if not os.path.exists(dirname):
        create_directory(dirname)
    codecs.open(target, "w", "utf-8").write(data)


@on_error("unable to write XML data %(2)s to %(1)s")
def write_xml(target, xml_data, pretty=False):
    """Write `xml_data` to a file `target`, optionally pretty-printed."""
    dirname = os.path.dirname(target)
    if not os.path.exists(dirname):
        create_directory(dirname)
    xml_data.write(target, xml_declaration=True, encoding="utf-8",
                   pretty_print=pretty)
    if not os.path.exists(target):
        raise IOError # because lxml's et.write() doesn't.

