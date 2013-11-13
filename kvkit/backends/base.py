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

# This is not to be used. Only as an example on how you should implement your
# backend.

# A backend could be a module, a class, whatever.

def init_class(cls):
  raise NotImplementedError

def init_document(self, **args):
  raise NotImplementedError

def index_keys_only(cls, field, start_value, end_value=None, **args):
  raise NotImplementedError

def index(cls, field, start_value, end_value=None, **args):
  raise NotImplementedError

def list_all_keys(cls, start_value=None, end_value=None, **args):
  raise NotImplementedError

def list_all(cls, start_value=None, end_value=None, **args):
  raise NotImplementedError

def clear_document(self):
  raise NotImplementedError

def get(cls, key, **args):
  raise NotImplementedError

def save(cls, key, data, **args):
  raise NotImplementedError

def delete(cls, key, **args):
  raise NotImplementedError

class BackendBase(object):
  def init_class(self, cls):
    raise NotImplementedError

  def init_document(self, doc, **args):
    raise NotImplementedError

  def index_keys_only(self, cls, field, start_value, end_value=None, **args):
    raise NotImplementedError

  def index(self, cls, field, start_value, end_value=None, **args):
    raise NotImplementedError

  def list_all_keys(self, cls, start_value=None, end_value=None, **args):
    raise NotImplementedError

  def list_all(self, cls, start_value=None, end_value=None, **args):
    raise NotImplementedError

  def clear_document(self, doc):
    raise NotImplementedError

  def get(self, cls, key, **args):
    raise NotImplementedError

  def save(self, cls, key, data, **args):
    raise NotImplementedError

  def delete(self, cls, key, **args):
    raise NotImplementedError
