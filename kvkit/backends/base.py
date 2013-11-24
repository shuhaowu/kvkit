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

# This is not to be used. Only as an example on how you should implement your
# backend.

# A backend could be a module, a class, whatever.

def init_class(cls):
  """Called right after a class has been initialized.

  Can be used to transform the class a little with backend specific metadata.
  Alternatively, you can use this to initialize your backend with information
  about the class rather than sticking the info right on the class.

  It is encouraged that if and when you transform classes, you use a namespace like
  cls.<backend>_meta = {} and stick your variables in there.

  Furthermore, this function should not fail when whatever variables you
  defined is not present because tests might set those options /after/ the
  class has already been initialized by the metaclass. The tests will set
  the variables and manually call ``init_class`` again.

  It could also be the case that this is a parent base class.

  Args:
    cls: The class that was just created.

  Returns:
    None

  Raises:
    Nothing. If you raise ``NotImplementedError`` here, nothing would work!
  """
  raise NotImplementedError

def init_document(self, **args):
  """Called right after a document has been initialized.

  Args:
    self: The document itself.
    **args: The additional keyword arguments passed in at ``Document.__init__``

  Returns:
    None

  Raises:
    Nothing. If you raise ``NotImplementedError`` here, nothing would work!
  """
  raise NotImplementedError

def index_keys_only(cls, field, start_value, end_value=None, **args):
  """Does an index operation but only return the keys.

  Args:
    cls: The class that the index operation is coming from.
    field: The field to query the index with.
    start_value: If ``end_value`` is None, this is the exact value to match.
        Otherwise this is the start value to match from.
    end_value: If not None, a range query is done. The range is:
        ``start_value <= matched <= end_value``.
    **args: Any additional keyword arguments passed in at ``Document.index_keys_only``.

  Returns:
    An iterator of keys only.

  Raises:
    kvkit.exceptions.NotIndexed if not indexed. This is optional, however, as
    backends might be able to index anyway..

  Note:
    This exists because some backends might have optimizations getting only
    keys as oppose to the document itself.
  """
  raise NotImplementedError

def index(cls, field, start_value, end_value=None, **args):
  """Does an index operation and returns the documents matched.

  Args:
    The same as ``index_keys_only``.

  Returns:
    An iterator for (key, json document, backend representation)

  Raises:
    kvkit.exceptions.NotIndexed if not indexed.

  Note:
    This could just be loading from index_keys_only. However, it should attempt
    to use backend-specific optimizations if available.
  """
  raise NotImplementedError

def list_all_keys(cls, start_value=None, end_value=None, **args):
  """Lists all the keys for this class.

  Args:
    cls: The class to list from.
    start_value: Sometimes you only want a range of these keys. This is the
        start value.
    end_value: The end value of the range. The range is
        ``start_value <= v <= end_value``.
    **args: additional keyword arguments passed in from
        ``Document.list_all_keys``.

  Returns:
    An iterator of all keys.

  Note:
    This exists because some backends might have optimizations getting only
    keys as oppose to the document itself.
  """
  raise NotImplementedError

def list_all(cls, start_value=None, end_value=None, **args):
  """List all the objects for this class.

  Args:
    The same as list_all_keys

  Returns:
    An iterator for (key, json document, backend_obj)

  Note:
    This could just be loading from list_all_keys. However, it should attempt
    to use backend-specific optimizations if available.
  """
  raise NotImplementedError

def clear_document(self, **args):
  """Called after the document gets cleared.

  Used for clearing meta/indexes, or whatever. Also needs to handle the
  clearing of the _backend_obj

  Args:
    self: The document

  Returns:
    None

  Raises:
    Nothing. If you raise ``NotImplementedError`` here, clearing wouldn't work!
  """
  raise NotImplementedError

def get(cls, key, **args):
  """Getting the json document from the backend.

  Args:
    cls: The class of document to get from.
    key: The key to get from
    **args: Any additional arguments passed from ``Document.get``

  Returns:
    (JSON document, backend representation of the object (like RiakObject))

  Note:
    This backend representation would be set as _backend_obj on the Document.

  Raises:
    NotFoundError if this is not found
  """
  raise NotImplementedError

def save(self, key, data, **args):
  """Saves a key and a json document into the backend.

  Args:
    self: The document object to be saved.
    key: The key to save
    data: The json document to save.
    **args: The arguments passed from ``doc.save()``

  Returns:
    None
  """
  raise NotImplementedError

def delete(cls, key, doc=None, **args):
  """Deletes cls key from the db.

  Args:
    cls: The class to delete from
    key: The key to delete
    doc: If the delete originated from a document, this will be pointing to
         the document instance.
    **args: additional arguments passed in from ``Document.delete_key`` or
        ``doc.delete()``.

  Returns:
    None

  Note:
    If the object does not exists in the backend, this will just return.
  """
  raise NotImplementedError

def post_deserialize(self, data):
  """Runs after deserializing an object.

  This is probably because the object has been loaded from the db.

  Args:
    self: The document object after deserializing.
    data: The original data deserialized.

  Returns:
    None

  Raise:
    None or else deserializing won't work.
  """
  raise NotImplementedError

class BackendBase(object):
  """This is a backend base that you can extend.

  Used for a class based approach. All documentations are the same as above,
  except the first argument is now ``self``, which refers to the class backend
  object.
  """
  def init_class(self, cls):
    pass

  def init_document(self, doc, **args):
    pass

  def index_keys_only(self, cls, field, start_value, end_value=None, **args):
    raise NotImplementedError

  def index(self, cls, field, start_value, end_value=None, **args):
    raise NotImplementedError

  def list_all_keys(self, cls, start_value=None, end_value=None, **args):
    raise NotImplementedError

  def list_all(self, cls, start_value=None, end_value=None, **args):
    raise NotImplementedError

  def clear_document(self, doc):
    pass

  def get(self, cls, key, **args):
    raise NotImplementedError

  def save(self, cls, key, data, **args):
    raise NotImplementedError

  def delete(self, doc, key, **args):
    raise NotImplementedError
