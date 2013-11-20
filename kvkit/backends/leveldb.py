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

"""This backend uses leveldb to store data.

Note that leveldb can only have one process accessing it. Therefore this might
not be a good idea if you need multiprocesses.
"""

from __future__ import absolute_import

try:
  import ujson as json
except ImportError:
  try:
    import simplejson as json
  except ImportError:
    import json

import plyvel

from ..exceptions import NotFoundError

index_key = lambda f, v: "{0}~{1}".format(f, v)

def clear_document(self, **args):
  self.__dict__["_leveldb_old_indexes"] = {}


def delete(cls, key, **args):
  pass


def get(cls, key, **args):
  value = cls._leveldb_meta["db"].get(key)
  if value is None:
    raise NotFoundError

  return json.loads(value)


def index(cls, field, start_value, end_value=None, **args):
  pass


def index_keys_only(cls, field, start_value, end_value=None, **args):
  pass


def init_class(cls):
  setattr(cls, "_leveldb_meta", {})

  def open_connections():
    db = cls._leveldb_options.get("db")
    indexdb = cls._leveldb_options.get("indexdb")
    if isinstance(db, basestring):
      cls._leveldb_meta["db"] = plyvel.DB(db, create_if_missing=True)

    if isinstance(indexdb):
      cls._leveldb_meta["indexdb"] = plyvel.DB(indexdb, create_if_missing=True)

  def close_connections():
    cls._leveldb_meta["db"].close()
    cls._leveldb_meta["indexdb"].close()

  cls.open_leveldb_connections = open_connections
  cls.open_leveldb_connections()

  cls.close_leveldb_connections = close_connections


def init_document(self, **args):
  pass


def list_all(cls, start_value=None, end_value=None, **args):
  pass


def list_all_keys(cls, start_value=None, end_value=None, **args):
  pass


def save(cls, key, data, **args):
  pass
