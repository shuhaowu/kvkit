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

"""This backend uses Riak to store data.

For more information about Riak, checkout https://basho.com/riak/.
"""

from __future__ import absolute_import

from ..exceptions import ValidationError, NotFoundError

def clear_document(self, **args):
  pass


def delete(cls, key, **args):
  pass


def get(cls, key, **args):
  pass


def index(cls, field, start_value, end_value=None, **args):
  pass


def index_keys_only(cls, field, start_value, end_value=None, **args):
  pass


def init_class(cls):
  pass


def init_document(self, **args):
  pass


def list_all(cls, start_value=None, end_value=None, **args):
  pass


def list_all_keys(cls, start_value=None, end_value=None, **args):
  pass


def save(cls, key, data, **args):
  pass
