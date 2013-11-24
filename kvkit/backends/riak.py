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
  available = True

from ..document import Document
from ..exceptions import ValidationError, NotFoundError

def clear_document(self, **args):
  pass


def delete(cls, key, doc=None, **args):
  pass


def get(cls, key, **args):
  robj = cls._riak_options["bucket"].get(key)


def index(cls, field, start_value, end_value=None, **args):
  pass


def index_keys_only(cls, field, start_value, end_value=None, **args):
  pass


def init_class(cls):
  if not hasattr(cls, "_riak_options"):
    return

  setattr(cls, "_riak_meta", {})

  bucket = cls._riak_options["bucket"]
  bucket.resolver = cls._riak_options["bucket"].get("resolver")

  # I feel like I am abusing python's reflection.
  def add_link(self, obj, tag=None):
    if isinstance(obj, Document):
      # Assuming the foreign object's backend is riak.
      obj = obj._riak_object
    self._riak_object.add_link(obj, tag)
    return self

  cls.add_link = add_link
  cls.links = property(get_links, set_links)

def init_document(self, **args):
  pass


def list_all(cls, start_value=None, end_value=None, **args):
  pass


def list_all_keys(cls, start_value=None, end_value=None, **args):
  pass


def save(self, key, data, **args):
  self._riak_object.data = data

  indexes = {}
  for name in self.__class__._indexes:
    indexes[name] = data.get(name)

  self._riak_object.indexes = indexes
