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

try:
  # We prefer ujson, then simplejson, then json
  import ujson as json
except ImportError:
  try:
    import simplejson as json
  except ImportError:
    import json

from .properties.standard import BaseProperty, StringProperty, NumberProperty, ReferenceProperty, ListProperty
from .helpers import walk_parents
from .exceptions import ValidationError

class EmDocumentMetaclass(type):
  def __new__(cls, clsname, parents, attrs):
    if clsname in ("Document", "EmDocument"):
      return type.__new__(cls, clsname, parents, attrs)

    meta = {}

    indexes = []

    all_parents = reversed(walk_parents(parents))

    for p_cls in all_parents:
      if hasattr(p_cls, "_meta"):
        meta.update(p_cls._meta)

      if hasattr(p_cls, "_indexes"):
        indexes += list(p_cls._indexes)

    for name in attrs.keys():
      if name == "_backend":
        continue

      if isinstance(attrs[name], BaseProperty):
        meta[name] = attrs.pop(name)
        if isinstance(meta[name], (StringProperty, NumberProperty, ListProperty, ReferenceProperty)) and meta[name]._index:
          indexes.append(name)

    attrs["_meta"] = meta
    attrs["defined_properties"] = meta.keys()
    attrs["_indexes"] = indexes
    return type.__new__(cls, clsname, parents, attrs)

  def __getattr__(self, name):
    if hasattr(self, "_meta") and name in self._meta:
      return self._meta[name]
    raise AttributeError("'{0}' does not exist for class '{1}'.".format(name, self.__name__))


class EmDocument(object):
  """Embedded document as a JSON object

  Class Variables:
    - `DEFINED_PROPERTIES_ONLY`: A boolean value indicating that the only
                                 properties allowed are the ones defined.
                                 Defaults to False. If a violation is found,
                                 an error will be raised on `serialize` (and
                                 `save` for Document) and False will be returned
                                 in `is_valid`. `invalids` will return
                                 `"_extra_props"` in the list.
    - defined_properties: A list of defined properties. For read only.
  """
  __metaclass__ = EmDocumentMetaclass

  DEFINED_PROPERTIES_ONLY = False

  def __init__(self, data={}):
    """Initializes a new EmDocument

    Args:
      data: A dictionary that's supposed to be initialized with the
            document as attributes.
    """
    self.clear()
    self.merge(data)

  def _validation_error(self, name, value):
    raise ValidationError("'{0}' doesn't pass validation for property '{1}'".format(value, name))

  def _attribute_not_found(self, name):
    raise AttributeError("Attribute '{0}' not found with '{1}'.".format(name, self.__class__.__name__))

  def serialize(self, dictionary=True, restricted=tuple()):
    """Serializes the object into a dictionary with all the proper conversions

    Args:
      dictionary: boolean. If True, this will return a dictionary, otherwise the
                  dictionary will be dumped by json.
      restricted: The properties to not output in the serialized output. Useful
                  in scenarios where you need to hide info from something.
                  An example would be you need to hide some sort of token from
                  the user but you need to return the object to them, without
                  the token. This defaults to tuple(), which means nothing is
                  restricted.
    Returns:
      A plain dictionary representation of the object after all the conversion
      to make it json friendly.
    """
    # Note that this doesn't call is_valid as it has built in validation.

    d = {}
    for name, value in self._data.iteritems():
      if name in restricted:
        continue
      if name in self._meta:
        if not self._meta[name].validate(value):
          self._validation_error(name, value)
        value = self._meta[name].to_db(value)
      elif self.DEFINED_PROPERTIES_ONLY:
        raise ValidationError("Property {} is not defined and {} has DEFINED_PROPERTIES_ONLY".format(name, self.__class__.__name__))

      d[name] = value

    return d if dictionary else json.dumps(d)

  def deserialize(self, data):
    """Deserializes the data. This uses the `from_db` method of all the
    properties. This differs from `merge` as this assumes that the data is from
    the database and will convert from db whereas merge assumes the the data
    is from input and will not do anything to it. (unless the property has
    `on_set`).

    Args:
      data: The data dictionary from the database.

    Returns:
      self, with its attributes populated.

    """
    converted_data = {}
    props_to_load = set()

    for name, value in data.iteritems():
      if name in self._meta:
        if self._meta[name].load_on_demand:
          props_to_load.add(name)
        else:
          value = self._meta[name].from_db(value)

      converted_data[name] = value

    self.merge(converted_data, True)
    self._props_to_load = props_to_load
    return self

  @classmethod
  def load(cls, data):
    """A convenient method that creates an object and deserializes the data.

    Args:
      data: The data to be deserialized

    Returns:
      A document with the data deserialized.
    """
    doc = cls()
    return doc.deserialize(data)

  def is_valid(self):
    """Test if all the attributes pass validation.

    Returns:
      True or False
    """
    for name in self._meta:
      if not self._validate_attribute(name):
        return False

    # Seems inefficient. Any better way to do this?
    if self.DEFINED_PROPERTIES_ONLY:
      for name in self._data:
        if name not in self._meta:
          return False

    return True

  def invalids(self):
    """Get all the attributes' names that are invalid.

    Returns:
      A list of attribute names that have invalid values.
    """
    invalid = []
    for name in self._meta:
      if not self._validate_attribute(name):
        invalid.append(name)

    # TODO: Refactor with is_valid
    if self.DEFINED_PROPERTIES_ONLY:
      for name in self._data:
        if name not in self._meta:
          invalid.append("_extra_props")
    return invalid

  def _validate_attribute(self, name):
    if name not in self._data:
      self._attribute_not_found(name)

    if name in self._meta:
      return self._meta[name].validate(self._data[name])

    return True

  def merge(self, data, merge_none=False):
    """Merge the data from a non-db source.

    This method treats all `None` values in data as if the key associated with
    that `None` value is not even present. This will cause us to automatically
    convert the value to that property's default value if available.

    If None is indeed what you want to merge as oppose to the default value
    for the property, set `merge_none` to `True`.

    Args:
      data: The data dictionary, a json string, or a foreign document to merge
            into the object.
      merge_none: Boolean. If set to True, None values will be merged as is
                  instead of being converted into the default value of that
                  property. Defaults to False.
    Returns:
      self
    """
    if isinstance(data, EmDocument):
      data = data._data
    elif isinstance(data, basestring):
      data = json.loads(data)

    for name, value in data.iteritems():
      if not merge_none and name in self._meta and value is None:
        continue
      self.__setattr__(name, value)

    return self

  def clear(self, to_default=True):
    """Clears the object. Set all attributes to default or nothing.

    Args:
      to_default: Boolean. If True, all properties defined will be set to its
                  default value. Otherwise the document will be empty.

    Returns:
      self
    """
    self._data = {}
    self._props_to_load = set()

    if to_default:
      for name, prop in self._meta.iteritems():
        self._data[name] = prop.default()
    else:
      for name, prop in self._meta.iteritems():
        self._data[name] = None

    return self

  def __setattr__(self, name, value):
    """Sets the attribute of the object and calls `on_set` of the property
    if the property is defined and it has an `on_set` method.

    Args:
      name: name of the attribute
      value: the value of that attribute to set to.
    """
    if name[0] == "_" or name == "key":
      self.__dict__[name] = value
      return

    if name in self._meta:
      if hasattr(self._meta[name], "on_set"):
        value = self._meta[name].on_set(value)

    self._data[name] = value

  def __getattr__(self, name):
    """Get an attribute from the document.
    Note that if a property is defined and the value is not set. This will
    always return None. (Also remember that if a value is not set by you it
    does not mean that it is not initialized to its default value.)

    Args:
      name: the name of the attribute.
    Returns:
      The value of the attribute.
    """
    if name in self._data:
      if name in self._props_to_load:
        self._data[name] = self._meta[name].from_db(self._data[name])
        self._props_to_load.discard(name)
      return self._data[name]
    self._attribute_not_found(name)

  def __delattr__(self, name):
    if name in self._data:
      if name in self._meta:
        self._data[name] = None
      else:
        del self._data[name]
    else:
      self._attribute_not_found(name)

  __setitem__ = __setattr__
  __getitem__ = __getattr__
  __delitem__ = __delattr__
