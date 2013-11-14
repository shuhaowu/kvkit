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
from datetime import datetime
import time

from .standard import BaseProperty, _NOUNCE

# Now, owl.
# ,___,  ,___,
# (O,O)  (O,O)
# /)_)    (_(\
#  ""      ""

# Less space than storing your whole string as we use ints.
# Probably will never use used.
# But why not.
class EnumProperty(BaseProperty):
  """Stores a choice out of some possible values.

  Stores in the database as 1, 2, 3 to save space. This is probably not
  really used as most of the time a string property is sufficient.
  """
  def __init__(self, possible_values, **args):
    """Initializes a new EnumProperty.

    Args:
      possible_values: A list of a values that are possible in strings.
          Only these values will be allowed to set to this after.
    """
    BaseProperty.__init__(self, **args)

    self._map_forwards = {}
    for i, v in enumerate(possible_values):
      self._map_forwards[v] = i
    self._map_backwards = possible_values

  def validate(self, value):
    return BaseProperty.validate(self, value) and (value is None or value in self._map_forwards)

  def to_db(self, value):
    return None if value is None else self._map_forwards[value]

  def from_db(self, value):
    return None if value is None else self._map_backwards[int(value)]

# Hey something that may be used!
class DateTimeProperty(BaseProperty):
  """Stores the datetime in UTC seconds since the unix epoch.

  Takes in a datetime.
  """
  def __init__(self, **args):
    BaseProperty.__init__(self, **args)
    if self._default is _NOUNCE:
      self._default = lambda: datetime.now()

  def validate(self, value):
    if not BaseProperty.validate(self, value):
      return False

    if value is None or isinstance(value, datetime):
      return True

    if isinstance(value, (long, int, float)): # timestamp
      try:
        datetime.fromtimestamp(value)
      except ValueError:
        return False
      else:
        return True

    return False

  def to_db(self, value):
    if value is None or isinstance(value, (long, int, float)):
      return value

    # We assume that value now have to be a datetime due to validate.
    return time.mktime(value.timetuple())

  def from_db(self, value):
    return None if value is None else datetime.fromtimestamp(value)


# Password stuffs... maybe used.. to make passwords not a hassle.
try:
  import bcrypt
except ImportError:
  import os
  from hashlib import sha256

  # TODO: switch default methods to generate keys. Get someone else to figure
  # out security of the following..
  # In theory the developer will never use this.......
  _p = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  def generate_salt():
    """Generates a random salt.

    If bcrypt is not installed, it uses os.urandom to select from
    a-Z0-9 with a length of 25.

    With bcrypt installed, it uses bcrypt.gensalt().

    MAKE SURE YOU ARE USING BCRYPT IN PRODUCTION IF YOU USE THIS.

    Returns:
      A salt.
    """
    n = 25 # 25 should be good?
    t = ""
    while n > 0:
      i = ord(os.urandom(1))
      while i >= 248:
        i = ord(os.urandom(1))
      i %= 62
      t += _p[i]
      n -= 1
    return t

  hash_password = lambda password, salt: sha256(password + salt).hexdigest()
  hash_password.__doc__ = """Takes a plaintext password and a salt and generates a hash.

  If bcrypt is installed, it uses bcrypt.hashpw.

  Without bcrypt, it uses sha256(password + salt).

  MAKE SURE YOU ARE USING BCRYPT IN PRODUCTION IF YOU USE THIS.

  Args:
    password: the plain text password
    salt: the salt.

  Returns:
    A hash.
  """
else:
  generate_salt = lambda: bcrypt.gensalt()
  hash_password = lambda password, salt: bcrypt.hashpw(password, salt)

class PasswordProperty(BaseProperty):
  """Password property that's secure if bcrypt is installed.

  MAKE SURE YOU ARE USING BCRYPT IN PRODUCTION IF YOU USE THIS.

  When the value is set (i.e. document.password = "mypassword"), a salt
  will automatically be generated and document.password from now on will
  {"salt": salt, "hash": hash}. This is how it will be stored into the
  db.
  """
  def on_set(self, value):
    if not isinstance(value, basestring):
      return TypeError("Password must be a basestring!")

    record = {}
    record["salt"] = generate_salt()
    record["hash"] = hash_password(value, record["salt"])
    return record

  @staticmethod
  def check_password(password, record):
    """Checks if a password matches a record.

    Args:
      password: the plain text password.
      record: The record in the db, which is in the format of {"salt": salt, "hash": hash}.

    Returns:
      True or false depending of the password is the right one or not.

    Note:
      Typically you would just do::

          PasswordProperty.check_password(req.forms["password"],
                                          user.password)

      or something to that effect.
    """
    return hash_password(password, record["salt"]) == record["hash"]
