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
import unittest
import time

from ...properties.fancy import (
  EnumProperty,
  DateTimeProperty,
  PasswordProperty,
  hash_password
)


class FancyPropertiesTest(unittest.TestCase):
  def test_enumprop(self):
    prop = EnumProperty(("ottawa", "toronto", "vancouver"))

    self.assertTrue(prop.validate("ottawa"))
    self.assertEquals(0, prop.to_db("ottawa"))
    self.assertEquals("ottawa", prop.from_db(0))

    self.assertTrue(prop.validate("toronto"))
    self.assertEquals(1, prop.to_db("toronto"))
    self.assertEquals("toronto", prop.from_db(1))

    self.assertTrue(prop.validate("vancouver"))
    self.assertEquals(2, prop.to_db("vancouver"))
    self.assertEquals("vancouver", prop.from_db(2))

    self.assertTrue(prop.validate(None))
    self.assertEquals(None, prop.to_db(None))
    self.assertEquals(None, prop.from_db(None))

    self.assertFalse(prop.validate("noexist"))

  def test_datetimeprop(self):
    prop = DateTimeProperty()

    now = datetime.now()
    now_stamp = time.mktime(now.timetuple())

    self.assertTrue(isinstance(prop.default(), datetime))

    self.assertTrue(prop.validate(now))
    self.assertEquals(now_stamp, prop.to_db(now))

    self.assertTrue(prop.validate(now_stamp))
    self.assertEquals(now_stamp, prop.to_db(now_stamp))
    self.assertEquals(now.timetuple(), prop.from_db(now_stamp).timetuple())

    self.assertTrue(prop.validate(None))
    self.assertEquals(None, prop.to_db(None))

    prop = DateTimeProperty(default=None)
    self.assertEquals(None, prop.default())

  def test_passwordprop(self):
    prop = PasswordProperty()
    pw = prop.on_set("password")
    self.assertTrue("salt" in pw)
    self.assertTrue("hash" in pw)

    # TODO: security tests?
    self.assertEquals(hash_password("password", pw["salt"]), pw["hash"])
