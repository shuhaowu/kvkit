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
  indexdb = cls._leveldb_meta["indexdb"]
  if end_value is None:
    ik = index_key(field, start_value)
    v = indexdb.get(ik)

    if v is None:
      keys = []
    else:
      keys = json.loads(v)

    for k in keys:
      yield cls(k).reload()

  else:
    with indexdb.iterator(start=start_value,
                          stop=end_value,
                          include_stop=True) as it:
      for _, keys in it:
        yield cls(k).reload()


def index_keys_only(cls, field, start_value, end_value=None, **args):
  indexdb = cls._leveldb_meta["indexdb"]
  if end_value is None:
    ik = index_key(field, start_value)
    v = indexdb.get(ik)
    if v is None:
      return []
    else:
      return json.loads(indexdb.get(ik))
  else:
    all_keys = []
    with indexdb.iterator(start=start_value,
                          stop=end_value,
                          include_stop=True) as it:
      for _, keys in it:
        all_keys.extend(json.loads(keys))

    return all_keys


def init_class(cls):
  if not hasattr(cls, "_leveldb_options"):
    # must be in test mode
    return

  setattr(cls, "_leveldb_meta", {})

  def open_connections(cls):

    db = cls._leveldb_options.get("db")
    indexdb = cls._leveldb_options.get("indexdb")
    if isinstance(db, basestring):
      cls._leveldb_meta["db"] = plyvel.DB(db, create_if_missing=True)

    if isinstance(indexdb, basestring):
      cls._leveldb_meta["indexdb"] = plyvel.DB(indexdb, create_if_missing=True)

  def close_connections(cls):
    if cls._leveldb_meta.get("db"):
      cls._leveldb_meta["db"].close()

    if cls._leveldb_meta.get("indexdb"):
      cls._leveldb_meta["indexdb"].close()

  cls.open_leveldb_connections = classmethod(open_connections)
  cls.open_leveldb_connections()

  cls.close_leveldb_connections = classmethod(close_connections)


def init_document(self, **args):
  pass


def list_all(cls, start_value=None, end_value=None, **args):
  pass


def list_all_keys(cls, start_value=None, end_value=None, **args):
  pass


def save(cls, key, data, **args):
  pass
