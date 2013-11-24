# -*- coding: utf-8 -*-
# This file is part of kvkit
#
# kvkit is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kvkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with kvkit. If not, see <http://www.gnu.org/licenses/>.

"""This backend uses Riak to store data.

For more information about Riak, checkout https://basho.com/riak/.
"""

from __future__ import absolute_import

try:
  import riak
except ImportError:
  available = False
else:
  from riak.resolver import default_resolver
  available = True

from ..document import Document
from ..exceptions import ValidationError, NotFoundError, NotIndexed
from ..properties import StringProperty, ListProperty, ReferenceProperty, NumberProperty

def clear_document(self, **args):
  self._backend_object = self.__class__._riak_options["bucket"].new(self.key)


def delete(cls, key, doc=None, **args):
  cls._riak_options["bucket"].delete(key, **args)


def get(cls, key, **args):
  robj = cls._riak_options["bucket"].get(key, **args)
  if robj.encoded_data is None:
    raise NotFoundError

  return robj.data, robj


def index(cls, field, start_value, end_value=None, **args):
  for key in index_keys_only(cls, field, start_value, end_value, **args):
    data, ro = get(cls, key)
    yield key, data, ro


def index_keys_only(cls, field, start_value, end_value=None, **args):
  if field not in ("$bucket", "$key"):
    if field not in cls._indexes:
      raise NotIndexed("Field '%field' not indexed.")

    if not field.endswith("_bin") and not field.endswith("_int"):
      if isinstance(cls._meta[field], (ReferenceProperty, StringProperty, ListProperty)):
        field += "_bin"
      elif isinstance(cls._meta[field], NumberProperty):
        if cls._meta[field].integer:
          field += "_int"
        else:
          field += "_bin"

  index_page = cls._riak_options["bucket"].get_index(field, start_value, end_value, return_terms=False, **args)
  keys_iterated = set()
  for key in index_page:
    if key in keys_iterated:
      continue
    keys_iterated.add(key)
    yield key


def init_class(cls):
  if not hasattr(cls, "_riak_options"):
    return

  setattr(cls, "_riak_meta", {})

  bucket = cls._riak_options["bucket"]
  bucket.resolver = cls._riak_options.get("resolver", default_resolver)

  # I feel like I am abusing python's reflection.
  def add_link(self, obj, tag=None):
    if isinstance(obj, Document):
      # Assuming the foreign object's backend is riak.
      obj = obj._backend_object
    self._backend_object.add_link(obj, tag)
    return self

  def get_links(self):
    return self._backend_object.links

  def set_links(self, value):
    self._backend_object.links = value

  cls.add_link = add_link
  cls.links = property(get_links, set_links)


def init_document(self, **args):
  pass


def list_all_keys(cls, start_value=None, end_value=None, **args):
  if start_value is None:
    start_value = "_"
  return index_keys_only(cls, "$bucket", start_value, end_value, **args)


def list_all(cls, start_value=None, end_value=None, **args):
  if start_value is None:
    start_value = "_"
  return index(cls, "$bucket", start_value, end_value, **args)


def save(self, key, data, **args):
  self._backend_object.data = data

  indexes = set()
  for name in self.__class__._indexes:
    if isinstance(self._meta[name], (StringProperty, ReferenceProperty)):
      indexes.add((name + "_bin", data[name]))
    elif isinstance(self._meta[name], ListProperty):
      field = name + "_bin"
      for value in data[name]:
        indexes.add((field, value))
    elif isinstance(self._meta[name], NumberProperty):
      if self._meta[name].integer:
        indexes.add((name + "_int", data[name]))
      else:
        indexes.add((name + "_bin", str(data[name])))

  self._backend_object.indexes = list(indexes)
  self._backend_object.store(**args)

def post_deserialize(self, data):
  pass
