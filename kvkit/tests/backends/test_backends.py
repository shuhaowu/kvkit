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

import unittest
import shutil

try:
  import riak
except ImportError:
  pass

from ...backends import leveldb, slow_memory
from ...backends import riak as riak_backend
from ...document import Document
from ...exceptions import NotFoundError
from ...properties.standard import (
    StringProperty,
    NumberProperty,
    ListProperty,
    ReferenceProperty
)

def setup_doc_class(cls, option_name=None, options=None):
  if option_name is not None:
    setattr(cls, option_name, options)

  cls._backend.init_class(cls)


def create_base_documents(backend, option_names=[None, None, None], options=[None, None, None]):
  # kinda hacky.
  class BaseDocument(Document):
    _backend = backend

  BaseDocument._backend = backend
  setup_doc_class(BaseDocument, option_names[0], options[0])

  class SimpleDocument(BaseDocument):
    string = StringProperty()
    number = NumberProperty()

  setup_doc_class(SimpleDocument, option_names[1], options[1])

  class DocumentWithIndexes(BaseDocument):
    string = StringProperty(index=True)
    list = ListProperty(index=True)
    ref = ReferenceProperty(SimpleDocument, index=True)
    number = NumberProperty(index=True)

  setup_doc_class(DocumentWithIndexes, option_names[2], options[2])

  return BaseDocument, SimpleDocument, DocumentWithIndexes


def create_testcase(BaseDocument, SimpleDocument, DocumentWithIndexes, name, cleanup=None):
  backend = BaseDocument._backend

  class BackendSpec(unittest.TestCase):

    def tearDown(self):
      if cleanup:
        cleanup()

    @classmethod
    def tearDownClass(cls):
      if cleanup:
        cleanup()

    def test_clear_document(self):
      doc = SimpleDocument()
      backend.clear_document(doc) # should just work

    def test_delete(self):
      backend.delete(SimpleDocument, "non-existent") # should work
      doc = SimpleDocument().save()
      backend.delete(SimpleDocument, doc.key)
      with self.assertRaises(NotFoundError):
        doc.reload()

    def test_get(self):
      with self.assertRaises(NotFoundError):
        backend.get(SimpleDocument, "non-existent")

      doc = SimpleDocument().save()
      v, _ = backend.get(SimpleDocument, doc.key)
      self.assertEquals(doc.serialize(), v)

    def test_index(self):

      # Testing no indexed
      results = list(backend.index(DocumentWithIndexes, "string", "abc"))
      self.assertEquals(0, len(results))

      # Testing single value
      doc1 = DocumentWithIndexes(data={"string": "abc"}).save()
      results = list(backend.index(DocumentWithIndexes, "string", "abc"))
      self.assertEquals(1, len(results))

      key, value, _ = results[0]
      self.assertEquals(key, doc1.key)
      self.assertEquals(value, doc1.serialize())

      # Testing multiple values
      doc2 = DocumentWithIndexes(data={"string": "bcd"}).save()
      results = list(backend.index(DocumentWithIndexes, "string", "abc", "bcd"))
      self.assertEquals(2, len(results))
      results.sort(key=lambda x: x[1]["string"])

      self.assertEquals("abc", results[0][1]["string"])
      self.assertEquals(doc1.key, results[0][0])
      self.assertEquals("bcd", results[1][1]["string"])
      self.assertEquals(doc2.key, results[1][0])

      # Testing number property
      doc3 = DocumentWithIndexes(data={"number": 4}).save()
      doc4 = DocumentWithIndexes(data={"number": 5.5}).save()
      doc5 = DocumentWithIndexes(data={"number": 6}).save()

      results = list(backend.index(DocumentWithIndexes, "number", 4, 5.5))
      self.assertEquals(2, len(results))
      results.sort(key=lambda x: x[1]["number"])
      self.assertEquals(4, results[0][1]["number"])
      self.assertEquals(5.5, results[1][1]["number"])

      # Testing list property

      doc6 = DocumentWithIndexes(data={"list": [1, 2, 3, "yay"]}).save()
      results = list(backend.index(DocumentWithIndexes, "list", 2))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0][0])

      results = list(backend.index(DocumentWithIndexes, "list", 2, 4))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0][0])

      results = list(backend.index(DocumentWithIndexes, "list", "yay"))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0][0])

      # Testing reference property

      sdoc = SimpleDocument().save()
      doc7 = DocumentWithIndexes(data={"ref": sdoc}).save()

      results = list(backend.index(DocumentWithIndexes, "ref", sdoc.key))
      self.assertEquals(1, len(results))
      self.assertEquals(doc7.key, results[0][0])

    def test_index_keys_only(self):
      # pretty much a straight copy from index. With some modifications

      # Testing no indexed
      results = list(backend.index_keys_only(DocumentWithIndexes, "string", "abc"))
      self.assertEquals(0, len(results))

      # Testing single value
      doc1 = DocumentWithIndexes(data={"string": "abc"}).save()

      results = list(backend.index_keys_only(DocumentWithIndexes, "string", "abc"))
      self.assertEquals(1, len(results))
      self.assertTrue(doc1.key in results)

      # Testing multiple values
      doc2 = DocumentWithIndexes(data={"string": "bcd"}).save()
      results = list(backend.index_keys_only(DocumentWithIndexes, "string", "abc", "bcd"))
      self.assertEquals(2, len(results))
      self.assertTrue(doc1.key in results)
      self.assertTrue(doc2.key in results)

      # Testing number property
      doc3 = DocumentWithIndexes(data={"number": 4}).save()
      doc4 = DocumentWithIndexes(data={"number": 5.5}).save()
      doc5 = DocumentWithIndexes(data={"number": 6}).save()


      results = list(backend.index_keys_only(DocumentWithIndexes, "number", 4, 5.5))
      self.assertEquals(2, len(results))
      self.assertTrue(doc3.key in results)
      self.assertTrue(doc4.key in results)

      # Testing list property

      doc6 = DocumentWithIndexes(data={"list": [1, 2, 3, "yay"]}).save()
      results = list(backend.index_keys_only(DocumentWithIndexes, "list", 2))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0])

      results = list(backend.index_keys_only(DocumentWithIndexes, "list", 2, 4))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0])

      results = list(backend.index_keys_only(DocumentWithIndexes, "list", "yay"))
      self.assertEquals(1, len(results))
      self.assertEquals(doc6.key, results[0])

      # Testing reference property

      sdoc = SimpleDocument().save()
      doc7 = DocumentWithIndexes(data={"ref": sdoc}).save()

      results = list(backend.index_keys_only(DocumentWithIndexes, "ref", sdoc.key))
      self.assertEquals(1, len(results))
      self.assertEquals(doc7.key, results[0])

    # def test_init_class(self):
    # def test_init_document(self):
    # These methods do not exist because they are tested during the course of
    # this test from initializing classes in the beginning and the documents

    def test_list_all_keys_no_pollution(self):
      doc1 = SimpleDocument().save()
      doc2 = DocumentWithIndexes().save()

      results = list(backend.list_all_keys(SimpleDocument))
      self.assertEquals(1, len(results))
      self.assertTrue(doc1.key in results)

      results = list(backend.list_all_keys(DocumentWithIndexes))
      self.assertEquals(1, len(results))
      self.assertTrue(doc2.key in results)

    def test_list_all(self):
      doc1 = SimpleDocument(data={"number": 1}).save()
      doc2 = SimpleDocument(data={"number": 2}).save()
      results = list(backend.list_all(SimpleDocument))

      self.assertEquals(2, len(results))
      results.sort(key=lambda x: x[1]["number"])
      self.assertEquals(doc1.key, results[0][0])
      self.assertEquals(doc1.serialize(), results[0][1])
      self.assertEquals(doc2.key, results[1][0])
      self.assertEquals(doc2.serialize(), results[1][1])

    def test_list_all_range(self):
      doc1 = SimpleDocument("1").save()
      doc2 = SimpleDocument("2").save()
      doc3 = SimpleDocument("3").save()

      results = backend.list_all(SimpleDocument, "1", "2")
      self.assertEquals(2, len(results))
      results.sort(key=lambda x: x[1]["number"])
      self.assertEquals(doc1.key, results[0][0])
      self.assertEquals(doc1.serialize(), results[0][1])
      self.assertEquals(doc2.key, results[1][0])
      self.assertEquals(doc2.serialize(), results[1][1])

    def test_list_all_keys(self):
      doc1 = SimpleDocument(data={"number": 1}).save()
      doc2 = SimpleDocument(data={"number": 2}).save()

      results = list(backend.list_all_keys(SimpleDocument))

      self.assertEquals(2, len(results))
      self.assertTrue(doc1.key in results)
      self.assertTrue(doc2.key in results)

    def test_list_all_range(self):
      doc1 = SimpleDocument("1").save()
      doc2 = SimpleDocument("2").save()
      doc3 = SimpleDocument("3").save()

      results = list(backend.list_all_keys(SimpleDocument, "1", "2"))

      self.assertEquals(2, len(results))
      self.assertTrue(doc1.key in results)
      self.assertTrue(doc2.key in results)

    # Seems a bit repetitive :P
    def test_save(self):
      doc1 = SimpleDocument("test-key", data={"number": 1})
      data = doc1.serialize()
      backend.save(doc1, "test-key", data)

      doc = SimpleDocument.get("test-key")
      self.assertEquals(1, doc.number)

  BackendSpec.__name__ = name
  return BackendSpec


# Slow memory tests

SlowMemoryBaseDocument, SimpleDocument, DocumentWithIndexes = create_base_documents(slow_memory)

SlowMemoryBackendTest = create_testcase(SlowMemoryBaseDocument,
                                        SimpleDocument,
                                        DocumentWithIndexes,
                                        "SlowMemoryBackendTest",
                                        slow_memory.cleardb)

# Leveldb tests

if leveldb.available:
  LevelDBBaseDocument, SimpleDocument, DocumentWithIndexes = create_base_documents(leveldb,
      (None, "_leveldb_options", "_leveldb_options"),
      (
        None,
        {"db": "dbs/test_simple_document"},
        {"db": "dbs/test_document_indexed", "indexdb": "dbs/test_document_indexed.indexes"}
      )
  )

  def leveldb_clear():
    SimpleDocument.close_leveldb_connections()
    DocumentWithIndexes.close_leveldb_connections()

    shutil.rmtree(SimpleDocument._leveldb_options["db"])
    shutil.rmtree(DocumentWithIndexes._leveldb_options["db"])
    shutil.rmtree(DocumentWithIndexes._leveldb_options["indexdb"])

    SimpleDocument.open_leveldb_connections()
    DocumentWithIndexes.open_leveldb_connections()

  LeveldbBackendTest = create_testcase(LevelDBBaseDocument,
                                       SimpleDocument,
                                       DocumentWithIndexes,
                                       "LeveldbBackendTest",
                                       leveldb_clear)

if riak_backend.available:
  client = riak.RiakClient()
  simple_bucket = client.bucket("test_kvkit_simple_document")
  indexed_bucket = client.bucket("test_kvkit_document_with_indexes")
  RiakBaseDocument, RiakSimpleDocument, RiakDocumentWithIndexes = create_base_documents(riak_backend,
      (None, "_riak_options", "_riak_options"),
      (None, {"bucket": simple_bucket}, {"bucket": indexed_bucket})
  )

  def riak_clear():
    for keylist in simple_bucket.stream_keys():
      for key in keylist:
        simple_bucket.delete(key)

    for keylist in indexed_bucket.stream_keys():
      for key in keylist:
        indexed_bucket.delete(key)

  RiakBackendTest = create_testcase(RiakBaseDocument,
                                    RiakSimpleDocument,
                                    RiakDocumentWithIndexes,
                                    "RiakBackendTest",
                                    riak_clear)