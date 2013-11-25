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

from __future__ import absolute_import

import json
import unittest

from ..document import Document, EmDocument
from ..exceptions import NotFoundError, ValidationError
from ..properties import (
    StringProperty,
    NumberProperty,
    ListProperty,
    ReferenceProperty
)

from ..backends import slow_memory

class BaseDocument(Document):
  _backend = slow_memory

class SimpleDocument(BaseDocument):
  s = StringProperty()
  i = NumberProperty()
  l = ListProperty()
  sr = StringProperty(required=True)
  sv = StringProperty(validators=lambda v: v == "valid")
  sd = StringProperty(default="default")

class SomeDocument(BaseDocument):
  test_str_index = StringProperty(index=True)
  test_number_index = NumberProperty(index=True)
  test_list_index = ListProperty(index=True)

class DocumentWithRef(BaseDocument):
  ref = ReferenceProperty(SomeDocument)

class DocumentLater(BaseDocument):
  pass

class DocumentWithLoadOnDemand(BaseDocument):
  d = ReferenceProperty(SimpleDocument, load_on_demand=True)

class Mixin(EmDocument):
  test = StringProperty(validators=lambda v: v == "test")
  test_index = StringProperty(index=True)

class DocumentWithMixin(BaseDocument, Mixin):
  pass

class BasicDocumentTest(unittest.TestCase):
  def tearDown(self):
    slow_memory.cleardb()

  def test_serialize_with_key(self):
    doc = DocumentLater()
    item = doc.serialize(include_key=True)
    self.assertTrue("key" in item)
    self.assertEquals(doc.key, item["key"])

    item = doc.serialize(include_key=True, dictionary=False)
    item = json.loads(item)
    self.assertTrue("key" in item)
    self.assertEquals(doc.key, item["key"])

  def test_save_get_delete(self):
    doc = SimpleDocument()
    doc.s = "mrrow"
    doc.i = 1337
    doc.l = ["123123", 123123]
    doc.sr = "lolwut"
    doc.sv = "valid"
    doc.save()

    doc2 = SimpleDocument.get(doc.key)
    self.assertEquals(doc.s, doc2.s)
    self.assertEquals(doc.i, doc2.i)
    self.assertEquals(doc.l, doc2.l)
    self.assertEquals(doc.sr, doc2.sr)
    self.assertEquals(doc.sv, doc2.sv)
    self.assertEquals("default", doc2.sd)

    doc.delete()
    with self.assertRaises(NotFoundError):
      doc2.reload()

  def test_document_mixin_indexes_inheritance(self):
    doc = DocumentWithMixin()
    doc.test = "test"
    doc.test_index = "a"
    doc.save()
    keys = DocumentWithMixin.index_keys_only("test_index", "a")
    self.assertEquals(1, len(keys))
    self.assertEquals(doc.key, keys[0])

  def test_document_mixin(self):
    doc = DocumentWithMixin()
    doc.test = "test"
    self.assertTrue(doc.is_valid())
    doc.test = "lols"
    self.assertFalse(doc.is_valid())
    doc.test = "test"
    doc.save()

    doc2 = DocumentWithMixin.get(doc.key)
    self.assertEqual("test", doc2.test)

  def test_reference_document(self):
    doc = SomeDocument()
    doc.save()

    doc2 = DocumentWithRef()
    doc2.ref = doc
    doc2.save()

    doc2_copy = DocumentWithRef.get(doc2.key)
    self.assertEquals(doc2.key, doc2_copy.key)
    self.assertEquals(doc.key, doc2_copy.ref.key)

  def test_load_on_demand(self):
    sdoc = SimpleDocument(data={"s": "yay", "sv": "valid", "sr": "required"})
    sdoc.save()
    doc = DocumentWithLoadOnDemand(data={"d": sdoc})
    doc.save()

    d = DocumentWithLoadOnDemand.get(doc.key)

    # Should be just a key
    self.assertTrue(isinstance(d._data["d"], basestring))
    self.assertEquals(sdoc.key, d.d.key)
    self.assertEquals(d.d.s, sdoc.s)


  def test_2i_save_delete(self):
    doc = SomeDocument()
    doc.test_str_index = "meow"
    doc.test_number_index = 1337
    doc.test_list_index = ["hello", "world", 123]
    doc.save()

    def _test_keys_only(self, doc, field, value):
      keys = SomeDocument.index_keys_only(field, value)

      if doc:
        self.assertEquals(1, len(keys))
        self.assertEquals(doc.key, keys[0])
      else:
        self.assertEquals(0, len(keys))

    _test_keys_only(self, doc, "test_list_index", "hello")
    _test_keys_only(self, doc, "test_list_index", "world")
    _test_keys_only(self, doc, "test_list_index", 123)
    _test_keys_only(self, doc, "test_str_index", "meow")
    _test_keys_only(self, doc, "test_number_index", 1337)

    doc.test_str_index = "quack"
    doc.test_number_index = 1336
    doc.test_list_index = ["hello", "wut"]
    doc.save()

    _test_keys_only(self, doc, "test_str_index", "quack")
    _test_keys_only(self, None, "test_str_index", "meow")
    _test_keys_only(self, doc, "test_number_index", 1336)
    _test_keys_only(self, None, "test_number_index", 1337)
    _test_keys_only(self, doc, "test_list_index", "hello")
    _test_keys_only(self, doc, "test_list_index", "wut")
    _test_keys_only(self, None, "test_list_index", "world")
    _test_keys_only(self, None, "test_list_index", 123)

    # This is really bad in practise. Divergent copies are bad.
    samedoc = SomeDocument.get(doc.key)
    del samedoc.test_list_index
    del samedoc.test_number_index
    samedoc.save()

    _test_keys_only(self, None, "test_list_index", "hello")
    _test_keys_only(self, None, "test_list_index", "wut")
    _test_keys_only(self, None, "test_number_index", 1336)

    samedoc.delete()

    _test_keys_only(self, None, "test_str_index", "quack")
    _test_keys_only(self, None, "test_number_index", 1336)

  def test_validation(self):
    # Test for required
    doc = SimpleDocument()
    doc.sv = "valid"

    with self.assertRaises(ValidationError):
      doc.save()

    # Test for validator fail
    doc = SimpleDocument()
    doc.sr = "yay"
    doc.sv = "invalid"
    with self.assertRaises(ValidationError):
      doc.save()

  def test_index_deserialized(self):
    ref = SomeDocument().save()
    doc = DocumentWithRef()
    doc.ref = ref
    doc.save()

    counter = 0
    for doc in DocumentWithRef.index("$bucket", None):
      counter += 1
      self.assertEquals(ref.key, doc.ref.key)

    self.assertEquals(1, counter)

  def test_2i_iterator(self):
    doc = SomeDocument()
    doc.test_str_index = "meow"
    doc.test_number_index = 1337
    doc.test_list_index = ["hello", "world", 123]
    doc.save()

    counter = 0
    for d in SomeDocument.index("test_str_index", "meow"):
      counter += 1
      self.assertEquals(doc.key, d.key)

    self.assertEquals(1, counter)

    counter = 0
    for d in SomeDocument.index("test_list_index", "hello", "world2"):
      counter += 1
      self.assertEquals(doc.key, d.key)

    self.assertEquals(1, counter)

  def test_equal(self):
    doc = SomeDocument("test")
    doc_same = SomeDocument("test")
    self.assertTrue(doc == doc_same)

    doc2 = SomeDocument(key="test1")
    self.assertFalse(doc == doc2)

  def test_index_keys(self):
    SomeDocument("1").save()
    SomeDocument("2").save()
    SomeDocument("3").save()
    SomeDocument("4").save()
    SomeDocument("5").save()

    keys = SomeDocument.index_keys_only("$key", "2", "4")
    self.assertEquals(3, len(keys))
    self.assertEquals("2", keys[0])
    self.assertEquals("3", keys[1])
    self.assertEquals("4", keys[2])

    keys = SomeDocument.index("$key", "1", "4")
    i = 1
    for doc in keys:
      self.assertEqual(str(i), doc.key)
      i += 1

    self.assertEquals(5, i)

  def test_set_key(self):
    doc = SomeDocument()
    k = doc.key
    doc.key = "hello"
    self.assertNotEquals(k, doc.key)
    self.assertEquals("hello", doc.key)

  def test_index_buckets(self):
    SomeDocument("1").save()
    SomeDocument("2").save()
    SomeDocument("3").save()
    SomeDocument("4").save()
    SomeDocument("5").save()

    # since we have no buckets, we need to pass in a value. None will do.
    keys = SomeDocument.index_keys_only("$bucket", None)
    self.assertEquals(5, len(keys))

    self.assertEqual("1", keys[0])
    self.assertEqual("2", keys[1])
    self.assertEqual("3", keys[2])
    self.assertEqual("4", keys[3])
    self.assertEqual("5", keys[4])

    i = 1
    for doc in SomeDocument.index("$bucket", None):
      self.assertEqual(str(i), doc.key)
      i += 1

    self.assertEquals(6, i)

if __name__ == "__main__":
  unittest.main()
