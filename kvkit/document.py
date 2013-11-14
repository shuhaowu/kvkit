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

from __future__ import absolute_import

try:
  import ujson as json
except ImportError:
  try:
    import simplejson as json
  except ImportError:
    import json

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
    doc = cls(key=key)
    doc.reload(**args)
    return doc

  @classmethod
  def get_or_new(cls, key, **args):
    try:
      return cls.get(key, **args)
    except NotFoundError:
      return cls(key=key)

  @classmethod
  def index_keys_only(cls, field, start_value, end_value=None, **args):
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
    return cls._backend.delete(cls.__class__, key, **args)

  @classmethod
  def list_all_keys(cls, start_value=None, end_value=None, **args):
    return cls._backend.list_all_keys(cls, start_value=start_value, end_value=end_value, **args)

  @classmethod
  def list_all(cls, start_value=None, end_value=None, **args):
    return cls._backend.list_all(cls, start_value, end_value, **args)

  @classmethod
  def index(cls, field, start_value, end_value=None, **args):
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
      yield cls(key=key, data=json.loads(value))

  def __init__(self, key=lambda: uuid1().hex, data={}, **args):
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
    value = self._backend.get(self.__class__, self.key, **args)
    value = json.loads(value)
    self.deserialize(value)
    return self

  def save(self, **args):
    value = json.dumps(self.serialize())
    self._backend.save(self.__class__, self.key, value, **args)
    return self

  def delete(self, **args):
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
