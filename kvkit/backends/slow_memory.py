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

import bisect
import json

from ..exceptions import NotFoundError

# Yay globals are terrible.
_db = {}

def cleardb():
  global _db
  _db = {}

# Yo Dawg. I heard you like tests so I wrote a test in your tests so you can
# test while you test.
# But seriously. I kinda need that right now.

def init_class(cls):
  pass

def init_document(self, **args):
  pass

def index(cls, field, start_value, end_value=None, **args):
  # slow implementation is okay for mock.
  kvs = []
  for k, v in _db.iteritems():
    v = json.loads(v)
    if field in v:
      if not isinstance(v[field], (list, tuple)):
        vfield = [v[field]]
      else:
        vfield = v[field]
      for fv in vfield:
        if fv >= start_value:
          if (end_value is None and fv == start_value) or fv <= end_value:
            kvs.append((k, json.dumps(v)))
            break

  return sorted(kvs)

def index_keys_only(cls, field, start_value, end_value=None, **args):
  kvs = index(cls, field, start_value, end_value, **args)
  return [k for k, _ in kvs]

def list_all_keys(cls, start_value=None, end_value=None, **args):
  keys = sorted(_db.keys())
  if start_value:
    try:
      start_i = bisect.bisect_left(keys, start_value)
    except ValueError:
      return []

    if end_value:
      end_i = bisect.bisect_right(keys, end_value)
      return keys[start_i:end_i]
    else:
      k = []
      while keys[start_i] == start_value:
        k.append(keys[start_i])
        start_i += 1

      return k
  else:
    return keys

def list_all(cls, start_value=None, end_value=None, **args):
  return [(k, _db[k])for k in list_all_keys(cls, start_value, end_value, **args)]

def clear_document(self):
  pass

def get(cls, key, **args):
  try:
    return _db[key]
  except KeyError:
    raise NotFoundError

def save(cls, key, data, **args):
  _db[key] = data

def delete(cls, key, **args):
  try:
    del _db[key]
  except KeyError:
    pass
