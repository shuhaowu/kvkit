# -*- coding: utf-8 -*-
# This file is part of kvkit
#
# Riakkit or Leveldbkit is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Riakkit or Leveldbkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Riakkit or Leveldbkit. If not, see <http://www.gnu.org/licenses/>.

"""
.. module:: kvkit.document
    :synopsis: Document class. The class that allows storing of data
               that you should extend from.

.. moduleauthor:: Shuhao Wu <shuhao@shuhaowu.com>
"""

from __future__ import absolute_import

from uuid import uuid1

from .emdocument import EmDocument, EmDocumentMetaclass
from .exceptions import NotFoundError
from .properties import NumberProperty

class DocumentMetaclass(EmDocumentMetaclass):
  def __new__(cls, clsname, parents, attrs):
    c = EmDocumentMetaclass.__new__(cls, clsname, parents, attrs)
    if clsname != "Document":
      if not hasattr(c, "_backend"):
        raise RuntimeError("You must specify a `_backend` to use Document")

      c._backend.init_class(c)
    return c

class Document(EmDocument):
  __metaclass__ = DocumentMetaclass

  @classmethod
  def get(cls, key, **args):
    """Gets an object from the db given a key.

    Args:
      key: The key

    Returns:
      The document.

    Raises:
      NotFoundError if not found.
    """
    doc = cls(key=key)
    doc.reload(**args)
    return doc

  @classmethod
  def get_or_new(cls, key, **args):
    """Gets an object from the db given a key. If fails, create one.

    Note that this method does not save the object, nor does it populate
    it.

    Args:
      key: The key

    Returns:
      The document. If it is not available from the db, a new one will
      be created.
    """
    try:
      return cls.get(key, **args)
    except NotFoundError:
      return cls(key=key)

  @classmethod
  def index_keys_only(cls, field, start_value, end_value=None, **args):
    """Uses the index to find document keys.

    Args:
      field: the property/field name.

      start_value: The value that you're indexing for. If an end_value
          is not provided, it has to be an exact match
          (field == start_value).

      end_value: the end value for a range query. If left to be None,
          it will match exact with start_value. Otherwise the range is
          start_value <= value <= end_value

    Returns:
      A list/iterator of keys that matches the query in arbitrary order
      that depends on the backend.
    """
    if field == "$bucket":
      return cls.list_all_keys()
    elif field == "$key":
      return cls.list_all_keys(start_value, end_value, **args)

    if isinstance(cls._meta[field], NumberProperty):
      start_value = float(start_value)
      if end_value is not None:
        end_value = float(end_value)

    return cls._backend.index_keys_only(cls, field, start_value, end_value, **args)

  @classmethod
  def delete_key(cls, key, **args):
    """Deletes a document with a key from the database.

    Args:
      key: The key to be deleted.

    Note:
      This is usually more efficient than YourDocument(key).delete() as
      that involves a get operation.
    """
    return cls._backend.delete(cls.__class__, key, **args)

  @classmethod
  def list_all_keys(cls, start_value=None, end_value=None, **args):
    """List all the keys from the db.

    Args:
      start_value: if specified, it will be the start of a range.
      end_value: if specified, it will be the end of a range.

    Returns:
      allkeys[start_value:] if only start_value is given,
      allkeys[start_value:end_value+1] if end_value is given. The +1 is
      largely a metaphor, as it will return all the values that ==
      end_value.
    """
    return cls._backend.list_all_keys(cls, start_value=start_value, end_value=end_value, **args)

  @classmethod
  def list_all(cls, start_value=None, end_value=None, **args):
    """List all the objects.

    Args:
      start_value: if specified, it will be the start of a range.
      end_value: if specified, it will be the end of a range.

    Returns:
      allobjs[start_value:] if only start_value is given,
      allobjs[start_value:end_value+1] if end_value is given. The +1 is
      largely a metaphor, as it will return all the values that ==
      end_value.
    """
    return cls._backend.list_all(cls, start_value, end_value, **args)

  @classmethod
  def index(cls, field, start_value, end_value=None, **args):
    """Uses the index to find documents that matches.

    Args:
      field: the property/field name.

      start_value: The value that you're indexing for. If an end_value
          is not provided, it has to be an exact match
          (field == start_value).

      end_value: the end value for a range query. If left to be None,
          it will match exact with start_value. Otherwise the range is
          start_value <= value <= end_value

    Returns:
      An iterator of loaded documents. Loaded at each iteration to save
      time and space.
    """
    kvs = []
    if field == "$bucket":
      kvs = cls.list_all()
    elif field == "$key":
      kvs = cls.list_all(start_value, end_value, **args)
    else:
      if isinstance(cls._meta[field], NumberProperty):
        start_value = float(start_value)
        if end_value is not None:
          end_value = float(end_value)

      kvs = cls._backend.index(cls, field, start_value, end_value, **args)

    for key, value in kvs:
      yield cls(key=key, data=value)

  def __init__(self, key=lambda: uuid1().hex, data={}, **args):
    """Initializes a new document.

    Args:
      key: A key for the object. Or a function that returns a key.
          By default it generates an uuid1 hex.

      data: The data to be merged in.

      **args: gets passed into EmDocument's __init__

    """
    if callable(key):
      key = key()

    if not isinstance(key, basestring):
      raise TypeError("Key must be a string, not {0}".format(key))

    self.__dict__["key"] = key
    EmDocument.__init__(self, data)

    self._backend.init_document(self, **args)

  def clear(self, to_default=True):
    EmDocument.clear(self, to_default)
    self._backend.clear_document(self)
    return self

  def reload(self, **args):
    """Reloads an object from the database.

    It will update inplace. Keyword arguments are passed to the backend.

    Returns:
      self

    Raises:
      NotFoundError
    """
    value = self._backend.get(self.__class__, self.key, **args)
    self.deserialize(value)
    return self

  def save(self, **args):
    """Saves an object into the db.

    Keyword arguments are passed to the backend.

    Returns:
      self

    Raises:
      ValidationError
    """
    value = self.serialize()
    self._backend.save(self.__class__, self.key, value, **args)
    return self

  def delete(self, **args):
    """Deletes this object from the db.

    Will also clear this document.

    Usually more efficient to use YourDocument.delete_key. However, if
    you already have the object loaded...

    Returns:
      self
    """
    self._backend.delete(self.__class__, self.key, **args)
    self.clear(False)
    return self

  def __eq__(self, other):
    """Check equality.

    However, this only checks if the key are the same and
    not the content. If the content is different and the key is the same this
    will return True.

    Args:
      other: The other document

    Returns:
      True if the two document's key are the same, False otherwise.
    """

    if isinstance(other, Document):
      return self.key == other.key

    return False
