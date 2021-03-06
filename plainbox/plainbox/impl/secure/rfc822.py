# This file is part of Checkbox.
#
# Copyright 2012, 2013 Canonical Ltd.
# Written by:
#   Sylvain Pineau <sylvain.pineau@canonical.com>
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.

#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`plainbox.impl.secure.rfc822` -- RFC822 parser
===================================================

Implementation of rfc822 serializer and deserializer.

.. warning::

    THIS MODULE DOES NOT HAVE STABLE PUBLIC API
"""

from functools import total_ordering
import inspect
import logging
import os
import re
import textwrap

from plainbox.abc import ITextSource
from plainbox.i18n import gettext as _

logger = logging.getLogger("plainbox.secure.rfc822")


@total_ordering
class UnknownTextSource(ITextSource):
    """
    A :class:`ITextSource` subclass indicating that the source of text is
    unknown.

    This instances of this class are constructed by gen_rfc822_records() when
    no explicit source is provided and the stream has no name. The serve as
    non-None values to prevent constructing :class:`PythonFileTextSource` with
    origin computed from :meth:`Origin.get_caller_origin()`
    """

    def __str__(self):
        return _("???")

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)

    def __eq__(self, other):
        if isinstance(other, UnknownTextSource):
            return True
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, UnknownTextSource):
            return False
        else:
            return NotImplemented


@total_ordering
class FileTextSource(ITextSource):
    """
    A :class:`ITextSource` subclass indicating that text came from a file.

    :ivar filename:
        name of the file something comes from
    """

    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return self.filename

    def __repr__(self):
        return "{}({!r})".format(
            self.__class__.__name__, self.filename)

    def __eq__(self, other):
        if isinstance(other, FileTextSource):
            return self.filename == other.filename
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, FileTextSource):
            return self.filename > other.filename
        else:
            return NotImplemented

    def relative_to(self, base_dir):
        """
        Compute a FileTextSource with the filename being a realtive path from
        the specified base directory.

        :param base_dir:
            A base directory name
        :returns:
            A new FileTextSource with filename relative to that base_dir
        """
        return self.__class__(os.path.relpath(self.filename, base_dir))


class PythonFileTextSource(FileTextSource):
    """
    A :class:`FileTextSource` subclass indicating the file was a python file.

    It implements no differences but in some context it might be helpful to
    differentiate on the type of the source field in the origin of a job
    definition record.

    :ivar filename:
        name of the python filename that something comes from
    """


@total_ordering
class Origin:
    """
    Simple class for tracking where something came from

    :ivar source:
        something that describes where the text came frome, technically it
        should be a :class:`~plainbox.abc.ITextSource` subclass but that
        interface defines just the intent, not any concrete API.

    :ivar line_start:
        the number of the line where the record begins

    :ivar line_end:
        the number of the line where the record ends
    """

    __slots__ = ['source', 'line_start', 'line_end']

    def __init__(self, source, line_start, line_end):
        self.source = source
        self.line_start = line_start
        self.line_end = line_end

    def __repr__(self):
        return "<{} source:{!r} line_start:{} line_end:{}>".format(
            self.__class__.__name__,
            self.source, self.line_start, self.line_end)

    def __str__(self):
        return "{}:{}-{}".format(
            self.source, self.line_start, self.line_end)

    def relative_to(self, base_dir):
        """
        Create a Origin with source relative to the specified base directory.

        :param base_dir:
            A base directory name
        :returns:
            A new Origin with source replaced by the result of calling
            relative_to(base_dir) on the current source *iff* the current
            source has that method, self otherwise.

        This method is useful for obtaining user friendly Origin objects that
        have short, understandable filenames.
        """
        if hasattr(self.source, 'relative_to'):
            return Origin(
                self.source.relative_to(base_dir),
                self.line_start, self.line_end)
        else:
            return self

    def __eq__(self, other):
        if isinstance(other, Origin):
            return ((self.source, self.line_start, self.line_end) ==
                    (other.source, other.line_start, other.line_end))
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Origin):
            return ((self.source, self.line_start, self.line_end) >
                    (other.source, other.line_start, other.line_end))
        else:
            return NotImplemented

    @classmethod
    def get_caller_origin(cls, back=0):
        """
        Create an Origin instance pointing at the call site of this method.
        """
        # Create an Origin instance that pinpoints the place that called
        # get_caller_origin().
        caller_frame, filename, lineno = inspect.stack(0)[2 + back][:3]
        try:
            source = PythonFileTextSource(filename)
            origin = Origin(source, lineno, lineno)
        finally:
            # Explicitly delete the frame object, this breaks the
            # reference cycle and makes this part of the code deterministic
            # with regards to the CPython garbage collector.
            #
            # As recommended by the python documentation:
            # http://docs.python.org/3/library/inspect.html#the-interpreter-stack
            del caller_frame
        return origin


def normalize_rfc822_value(value):
    # Remove the multi-line dot marker
    value = re.sub('^(\s*)\.$', '\\1', value, flags=re.M)
    # Remove consistent indentation
    value = textwrap.dedent(value)
    # Strip the remaining whitespace
    value = value.strip()
    return value


class RFC822Record:
    """
    Class for tracking RFC822 records.

    This is a simple container for the dictionary of data. The data is
    represented by two copies, one original and one after value normalization.
    Value normalization strips out excess whitespace and processes the magic
    leading dot syntax that is essential for empty newlines.

    Comparison is performed on the normalized data only, raw data is stored for
    reference but does not differentiate records.

    Each instance also holds the origin of the data (location of the
    file/stream where it was parsed from).
    """

    def __init__(self, data, origin=None, raw_data=None):
        """
        Initialize a new record.

        :param data:
            A dictionary with normalized record data
        :param origin:
            A :class:`Origin` instance that describes where the data came from
        :param raw_data:
            An optional dictionary with raw record data. If omitted then it
            will default to normalized data (as the same object, without making
            a copy)
        """
        self._data = data
        if raw_data is None:
            raw_data = data
        self._raw_data = raw_data
        if origin is None:
            origin = Origin.get_caller_origin()
        self._origin = origin

    def __repr__(self):
        return "<{} data:{!r} origin:{!r}>".format(
            self.__class__.__name__, self._data, self._origin)

    def __eq__(self, other):
        if isinstance(other, RFC822Record):
            return (self._data, self._origin) == (other._data, other._origin)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, RFC822Record):
            return (self._data, self._origin) != (other._data, other._origin)
        return NotImplemented

    @property
    def data(self):
        """
        The normalized version of the data set (dictionary)

        This property exposes the normalized version of the data encapsulated
        in this record. Normalization is performed with
        :func:`normalize_rfc822_value()`. Only values are normalized, keys are
        left intact.
        """
        return self._data

    @property
    def raw_data(self):
        """
        The raw version of data set (dictionary)

        This property exposes the raw (original) version of the data
        encapsulated by this record. This data is as it was originally parsed,
        including all the whitespace layout.

        In some records this may be 'normal' data object itself (same object).
        """
        return self._raw_data

    @property
    def origin(self):
        """
        The origin of the record.
        """
        return self._origin

    def dump(self, stream):
        """
        Dump this record to a stream
        """
        def _dump_part(stream, key, values):
            stream.write("%s:\n" % key)
            for value in values:
                if not value:
                    stream.write(" .\n")
                elif value == ".":
                    stream.write(" ..\n")
                else:
                    stream.write(" %s\n" % value)
        for key, value in self.data.items():
            if isinstance(value, (list, tuple)):
                _dump_part(stream, key, value)
            elif isinstance(value, str) and "\n" in value:
                values = value.split("\n")
                if not values[-1]:
                    values = values[:-1]
                _dump_part(stream, key, values)
            else:
                stream.write("%s: %s\n" % (key, value))
        stream.write("\n")


class RFC822SyntaxError(SyntaxError):
    """
    SyntaxError subclass for RFC822 parsing functions
    """

    def __init__(self, filename, lineno, msg):
        self.filename = filename
        self.lineno = lineno
        self.msg = msg

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(
            self.__class__.__name__, self.filename, self.lineno, self.msg)

    def __eq__(self, other):
        if isinstance(other, RFC822SyntaxError):
            return ((self.filename, self.lineno, self.msg)
                    == (other.filename, other.lineno, other.msg))
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, RFC822SyntaxError):
            return ((self.filename, self.lineno, self.msg)
                    != (other.filename, other.lineno, other.msg))
        return NotImplemented

    def __hash__(self):
        return hash((self.filename, self.lineno, self.msg))


def load_rfc822_records(stream, data_cls=dict, source=None):
    """
    Load a sequence of rfc822-like records from a text stream.

    :param stream:
        A file-like object from which to load the rfc822 data
    :param data_cls:
        The class of the dictionary-like type to hold the results. This is
        mainly there so that callers may pass collections.OrderedDict.
    :param source:
        A :class:`plainbox.abc.ITextSource` subclass instance that describes
        where stream data is coming from. If None, it will be inferred from the
        stream (if possible). Specialized callers should provider a custom
        source object to allow developers to accurately keep track of where
        (possibly problematic) RFC822 data is coming from. If this is None and
        inferring fails then all of the loaded records will have a None origin.

    Each record consists of any number of key-value pairs. Subsequent records
    are separated by one blank line. A record key may have a multi-line value
    if the line starts with whitespace character.

    Returns a list of subsequent values as instances RFC822Record class.  If
    the optional data_cls argument is collections.OrderedDict then the values
    retain their original ordering.
    """
    return list(gen_rfc822_records(stream, data_cls, source))


def gen_rfc822_records(stream, data_cls=dict, source=None):
    """
    Load a sequence of rfc822-like records from a text stream.

    :param stream:
        A file-like object from which to load the rfc822 data
    :param data_cls:
        The class of the dictionary-like type to hold the results. This is
        mainly there so that callers may pass collections.OrderedDict.
    :param source:
        A :class:`plainbox.abc.ITextSource` subclass instance that describes
        where stream data is coming from. If None, it will be inferred from the
        stream (if possible). Specialized callers should provider a custom
        source object to allow developers to accurately keep track of where
        (possibly problematic) RFC822 data is coming from. If this is None and
        inferring fails then all of the loaded records will have a None origin.

    Each record consists of any number of key-value pairs. Subsequent records
    are separated by one blank line. A record key may have a multi-line value
    if the line starts with whitespace character.

    Returns a list of subsequent values as instances RFC822Record class. If
    the optional data_cls argument is collections.OrderedDict then the values
    retain their original ordering.
    """
    record = None
    key = None
    value_list = None
    origin = None
    # If the source was not provided then try constructing a FileTextSource
    # from the name of the stream. If that fails, keep using None.
    if source is None:
        try:
            source = FileTextSource(stream.name)
        except AttributeError:
            source = UnknownTextSource()

    def _syntax_error(msg):
        """
        Report a syntax error in the current line
        """
        try:
            filename = stream.name
        except AttributeError:
            filename = None
        return RFC822SyntaxError(filename, lineno, msg)

    def _new_record():
        """
        Reset local state to track new record
        """
        nonlocal key
        nonlocal value_list
        nonlocal record
        nonlocal origin
        key = None
        value_list = None
        if source is not None:
            origin = Origin(source, None, None)
        record = RFC822Record(data_cls(), origin, data_cls())

    def _commit_key_value_if_needed():
        """
        Finalize the most recently seen key: value pair
        """
        nonlocal key
        if key is not None:
            raw_value = ''.join(value_list)
            normalized_value = normalize_rfc822_value(raw_value)
            record.raw_data[key] = raw_value
            record.data[key] = normalized_value
            logger.debug(_("Committed key/value %r=%r"), key, normalized_value)
            key = None

    def _set_start_lineno_if_needed():
        """
        Remember the line number of the record start unless already set
        """
        if origin and record.origin.line_start is None:
            record.origin.line_start = lineno

    def _update_end_lineno():
        """
        Update the line number of the record tail
        """
        if origin:
            record.origin.line_end = lineno

    # Start with an empty record
    _new_record()
    # Support simple text strings
    if isinstance(stream, str):
        # keepends=True (python3.2 has no keyword for this)
        stream = iter(stream.splitlines(True))
    # Iterate over subsequent lines of the stream
    for lineno, line in enumerate(stream, start=1):
        logger.debug(_("Looking at line %d:%r"), lineno, line)
        # Treat # as comments
        if line.startswith("#"):
            pass
        # Treat empty lines as record separators
        elif line.strip() == "":
            # Commit the current record so that the multi-line value of the
            # last key, if any, is saved as a string
            _commit_key_value_if_needed()
            # If data is non-empty, yield the record, this allows us to safely
            # use newlines for formatting
            if record.data:
                logger.debug(_("yielding record: %r"), record)
                yield record
            # Reset local state so that we can build a new record
            _new_record()
        # Treat lines staring with whitespace as multi-line continuation of the
        # most recently seen key-value
        elif line.startswith(" "):
            if key is None:
                # If we have not seen any keys yet then this is a syntax error
                raise _syntax_error(_("Unexpected multi-line value"))
            # Strip the initial space. This matches the behavior of xgettext
            # scanning our job definitions with multi-line values.
            line = line[1:]
            # Append the current line to the list of values of the most recent
            # key. This prevents quadratic complexity of string concatenation
            value_list.append(line)
            # Update the end line location of this record
            _update_end_lineno()
        # Treat lines with a colon as new key-value pairs
        elif ":" in line:
            # Since this is actual data let's try to remember where it came
            # from. This may be a no-operation if there were any preceding
            # key-value pairs.
            _set_start_lineno_if_needed()
            # Since we have a new, key-value pair we need to commit any
            # previous key that we may have (regardless of multi-line or
            # single-line values).
            _commit_key_value_if_needed()
            # Parse the line by splitting on the colon, getting rid of
            # all surrounding whitespace from the key and getting rid of the
            # leading whitespace from the value.
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.lstrip()
            # Check if the key already exist in this message
            if key in record.data:
                raise _syntax_error(_(
                    "Job has a duplicate key {!r} "
                    "with old value {!r} and new value {!r}"
                ).format(key, record.raw_data[key], value))
            if value.strip() != "":
                # Construct initial value list out of the (only) value that we
                # have so far. Additional multi-line values will just append to
                # value_list
                value_list = [value]
            else:
                # The initial line may be empty, in that case the spaces and
                # newlines there are discarded
                value_list = []
            # Update the end-line location
            _update_end_lineno()
        # Treat all other lines as syntax errors
        else:
            raise _syntax_error(
                _("Unexpected non-empty line: {!r}").format(line))
    # Make sure to commit the last key from the record
    _commit_key_value_if_needed()
    # Once we've seen the whole file return the last record, if any
    if record.data:
        logger.debug(_("yielding record: %r"), record)
        yield record
