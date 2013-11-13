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

import unittest

from ..helpers import walk_parents, mediocre_copy

class Document(object):
  # Just to test
  pass

class HelpersTest(unittest.TestCase):
  def test_walk_parents(self):
    class Parent(Document): pass
    class Child(Parent): pass

    parents = walk_parents([Child])
    self.assertEquals(2, len(parents))
    self.assertTrue(Parent in parents)
    self.assertTrue(Child in parents)

    class Child2(Child, Parent): pass

    parents = walk_parents([Child2])
    self.assertEquals(3, len(parents))
    self.assertTrue(Parent in parents)
    self.assertTrue(Child in parents)
    self.assertTrue(Child2 in parents)

    class Child3(Child2): pass
    parents = walk_parents([Child3])
    self.assertEquals(4, len(parents))
    self.assertTrue(Parent in parents)
    self.assertTrue(Child in parents)
    self.assertTrue(Child3 in parents)
    self.assertTrue(Child2 in parents)

  def test_mediocre_copy(self):
    l1 = [1, 2, 3, 4]
    self.assertEquals(l1, mediocre_copy(l1))

    l2 = [1, [2, 3], {1: 2}, (2, 3)]
    l2c = mediocre_copy(l2)
    self.assertFalse(l2c[1] is l2[1])
    l2c[1][1] = 3
    self.assertEquals([2, 3], l2[1])

    self.assertFalse(l2c[2] is l2[2])
    self.assertFalse(l2c[3] is l2[3])

    l3 = [1, [2, [3]], {1: {1: 2}}, (2, (3, 4))]
    l3c = mediocre_copy(l3)
    self.assertFalse(l3c[1][1] is l3[1][1])
    self.assertFalse(l3c[2][1] is l3[2][1])
    self.assertFalse(l3c[3][1] is l3[3][1])
