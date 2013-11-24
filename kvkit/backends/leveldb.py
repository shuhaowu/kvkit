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
"""This backend uses leveldb to store data.

Note that leveldb can only have one process accessing it. Therefore this might
not be a good idea if you need multiprocesses.
"""

from __future__ import absolute_import

from copy import copy
try:
  import ujson as json
except ImportError:
  try:
    import simplejson as json
  except ImportError:
    import json

try:
  import plyvel
except ImportError:
  available = False
else:
  available = True

from ..exceptions import NotFoundError


index_key = lambda f, v: "{0}~{1}".format(f, v)


def clear_document(self, **args):
  self.__dict__["_leveldb_old_indexes"] = {}


def get(cls, key, **args):
  key = str(key)

  value = cls._leveldb_meta["db"].get(key)
  if value is None:
    raise NotFoundError

  return json.loads(value), None


def _ensure_indexdb_exists(cls):
  if not cls._leveldb_meta.get("indexdb"):
    raise RuntimeError("DB for indexes are not defined for class '{0}'.".format(cls.__name__))


def index(cls, field, start_value, end_value=None, **args):
  _ensure_indexdb_exists(cls)

  indexdb = cls._leveldb_meta["indexdb"]
  if end_value is None:
    ik = index_key(field, start_value)
    v = indexdb.get(ik)

    if v is None:
      keys = []
    else:
      keys = json.loads(v)

    for k in keys:
      v, o = get(cls, k)
      yield k, v, o

  else:
    it = indexdb.iterator(start=index_key(field, start_value),
                          stop=index_key(field, end_value),
                          include_stop=True,
                          include_key=False)
    # to avoid awkward scenarios where two index values have the same obj
    keys_iterated = set()
    for keys in it:
      for k in json.loads(keys):
        if k not in keys_iterated:
          keys_iterated.add(k)
          v, o = get(cls, k)
          yield k, v, o


def index_keys_only(cls, field, start_value, end_value=None, **args):
  _ensure_indexdb_exists(cls)

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
    it = indexdb.iterator(start=index_key(field, start_value),
                          stop=index_key(field, end_value),
                          include_stop=True,
                          include_key=False)
    for keys in it:
      all_keys.extend(json.loads(keys))

    return list(set(all_keys))


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
  with cls._leveldb_meta["db"].iterator(start=start_value, stop=end_value, include_stop=True) as it:
    for key, value in it:
      yield key, json.loads(value), None


def list_all_keys(cls, start_value=None, end_value=None, **args):
  with cls._leveldb_meta["db"].iterator(start=start_value, stop=end_value, include_value=False, include_stop=True) as it:
    for key in it:
      yield key

def _build_indexes(cls, data):
  indexes = {}
  for name in cls._indexes:
    indexes[name] = copy(data.get(name))
  return indexes

def _figure_out_index_writes(idb, key, old, new):
  # Here be the dragons... Actually it is not /that/ bad.
  # If there is two copies of the same object and both saved without knowing
  # each other, that would be disastrous.

  wb = idb.write_batch()

  def add_index(field, value):
    if value is None:
      return # value is already none.. Do not index.

    keys = idb.get(index_key(field, value), [])
    if key not in keys:
      keys.append(key)
      wb.put(index_key(field, value), json.dumps(keys))


  def remove_index(field, value):
    keys = idb.get(index_key(field, value))
    if keys is None:
      return # Already removed

    keys = json.loads(keys)

    try:
      keys.remove(key)
    except ValueError:
      return # Already removed

    if len(keys) == 0:
      wb.delete(index_key(field, value))
    else:
      wb.put(index_key(field, value), json.dumps(keys))

  for field, value in old.iteritems():
    if isinstance(value, (list, tuple)):
      old_values = set(value)
      new_values = set(new.get(field, []))

      for v in (old_values - new_values):
        remove_index(field, v)
      for v in (new_values - old_values):
        add_index(field, v)
    else:
      if field not in new:
        remove_index(field, value)
      else:
        if value != new[field]:
          remove_index(field, value)
          # None values should be handled by add_index and
          # it should simply return.
          add_index(field, new[field])

  # Now we need to take a look at the new dictionary and make sure to add
  # anything that we missed. We already noted the change in field as well as
  # any field that is removed and became None in the lines above.

  for field, value in new.iteritems():
    if field not in old:
      # TODO: refactor
      if isinstance(value, (list, tuple)):
        for v in value:
          add_index(field, v)
      else:
        add_index(field, value)

  return wb

def save(self, key, data, **args):
  index_writebatch = None
  if self._leveldb_meta.get("indexdb"):
    new_indexes = _build_indexes(self.__class__, data)
    index_writebatch = _figure_out_index_writes(self._leveldb_meta["indexdb"],
                                                key,
                                                self._leveldb_old_indexes,
                                                new_indexes)
    # BUG: (?) Is it possible to fail something so badly that the _old_indexes
    # never gets flushed? Hopefully not.
    self._leveldb_old_indexes = new_indexes

  self._leveldb_meta["db"].put(key, json.dumps(data))

  if index_writebatch:
    index_writebatch.write()


def delete(cls, key, doc=None, **args):

  # There is an inherit danger to use delete_key without knowing about the
  # indexes. This is why in the leveldb delete, we always will load it first.
  if doc is None:
    try:
      doc = cls.get(key)
    except NotFoundError:
      return

  index_writebatch = None
  if doc._leveldb_meta.get("indexdb"):
    index_writebatch = _figure_out_index_writes(doc._leveldb_meta["indexdb"],
                                                key,
                                                doc._leveldb_old_indexes,
                                                {})
    doc._leveldb_old_indexes = {}

  doc._leveldb_meta["db"].delete(key)
  if index_writebatch:
    index_writebatch.write()


def post_deserialize(self, data):
  if self._leveldb_meta.get("indexdb"):
    self._leveldb_old_indexes = _build_indexes(self.__class__, data)
