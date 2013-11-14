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
from ..exceptions import NotFoundError

_NOUNCE = object()

class BaseProperty(object):
  def __init__(self, required=False, default=_NOUNCE,
               validators=[], load_on_demand=False,
               index=False):
    """The base property that all other properties extends from.

    Args:
      required: If True and if a value is None, save will raise a
          ValidationError. Defaults to False.
      default: The default value that document populates when it creates
          a new object. It could be a function that takes no arguments
          that returns a value to be filled as a default value. If this
          is not given, no default value is specified, the default value
          for that property will be None.
      validators: A function or a list of functions that takes a value
          and returns True or False depending on if the value is valid
          or not. If a function returns False, save will fail with
          ValidationError and is_valid will return False. Defaults to []
      load_on_demand: If True, the value will not be deserialized until
          the programmer accesses the value. Defaults to False, which
          means value will be deserialized when the object is loaded
          from the DB.
      index: If True, the database backend will create an index for this
          entry allowing it to be queried via index. This is only valid
          for StringProperty, NumberProperty, ListProperty, and
          ReferenceProperty. Individual backends may have more but will
          not necessarily be portable.
    """
    self.required = required
    self._default = default
    self._validators = validators
    self.load_on_demand = load_on_demand
    self._index = index

  def validate(self, value):
    """Validates a value.

    This invokes both the builtin validator as well as the custom
    validators. The BaseProperty version only validates with custom ones
    if available.

    Args:
      value: The value to be validated.

    Returns:
      True or False depending on if the value is valid or not.

    Note:
      If you are writing your own property class, subclass this one
      and in the validate method, put the following first to validate
      the custom validators::

        if not BaseProperty.validate(self, value):
          return False
    """
    if value is None:
      return not self.required

    if callable(self._validators):
      return self._validators(value)
    elif isinstance(self._validators, (list, tuple)):
      for validator in self._validators:
        if not validator(value):
          return False

    return True

  def to_db(self, value):
    """ Converts a value to a database friendly format (serialization).

    This should never convert None into anything else.

    Args:
      value: The value to be converted

    Returns:
      Whatever the property wants to do to that value. The BaseProperty
      version does nothing and just returns the value.

    Note:
      If you want to implement this version yourself it the return value
      of this should be JSON friendly. Do not convert None unless you
      absolutely mean it.
    """
    return value

  def from_db(self, value):
    """ Converts the value from to_db back into its original form.

    This should be the inverse function of to_db and it also shouldn't
    convert None into anything else other than itself.

    Args:
      value: Value from the database

    Returns:
      Whatever that type wants to be once its in application code rather
      than the db form.

    Note:
      It is important if you want to implement this that it is actually
      and inverse function of to_db. Do not convert None unless you
      absolutely mean it.

      If load_on_demand is True, this method will only be called the
      first time when the property is accessed.
    """
    return value

  def default(self):
    """Returns the default value of the property.

    It will first try to return the default you set (either function or
    value). If not it will return None.

    Returns:
      The default value specified by you or the type. Or None.
    """
    if callable(self._default):
      return self._default()

    return None if self._default is _NOUNCE else self._default

# Alias this for simplicity when declaring a dynamic property.
Property = BaseProperty

# standard properties... boring stuff
# This are strict, if you want to relax, use Property instead.

class StringProperty(BaseProperty):
  """For storing strings.

  Converts all value into unicode when serialized. Deserializes all to
  unicode as well.
  """
  def to_db(self, value):
    return None if value is None else unicode(value)

class NumberProperty(BaseProperty):
  """For storing real numbers.

  This always converts to a floating point.
  """

  def validate(self, value):
    """Checks if value is a number by taking `float(value)`.
    """
    if not BaseProperty.validate(self, value):
      return False

    if value is None:
      return True

    try:
      float(value)
    except (TypeError, ValueError):
      return False
    else:
      return True

  def to_db(self, value):
    return None if value is None else float(value)

class BooleanProperty(BaseProperty):
  """Boolean property. Values will be converted to boolean upon save.
  """
  def to_db(self, value):
    return None if value is None else bool(value)

class DictProperty(BaseProperty):
  """Dictionary property. Or a JSON object when stored.

  Value must be an instance of a dictionary (or subclass).
  """
  def __init__(self, **args):
    BaseProperty.__init__(self, **args)
    if self._default is _NOUNCE:
      self._default = lambda: {}

  def validate(self, value):
    return BaseProperty.validate(self, value) and (value is None or isinstance(value, dict))

class ListProperty(BaseProperty):
  """List property.

  Value must be an instance of a list/tuple (or subclass).
  """
  def __init__(self, **args):
    BaseProperty.__init__(self, **args)
    if self._default is _NOUNCE:
      self._default = lambda: []

  def validate(self, value):
    return BaseProperty.validate(self, value) and (value is None or isinstance(value, (tuple, list)))

class EmDocumentProperty(BaseProperty):
  """Embedded document property.

  Value must be an EmDocument or a dictionary"""
  def __init__(self, emdocument_class, **args):
    """Initializes a new embedded document property.

    Args:
      emdocument_class: The EmDocument child class.
      Everything else are inheritted from BaseProperty
    """
    BaseProperty.__init__(self, **args)
    self.emdocument_class = emdocument_class

  def validate(self, value):
    return BaseProperty.validate(self, value) and \
           (value is None or \
              (isinstance(value, self.emdocument_class) and \
               value.is_valid()))

  def to_db(self, value):
    return None if value is None else value.serialize()

  def from_db(self, value):
    return None if value is None else self.emdocument_class.load(value)

class EmDocumentsListProperty(BaseProperty):
  """A list of embedded documents.

  Probably shouldn't abuse this.
  """
  def __init__(self, emdocument_class, **args):
    """Initializes a new embedded document property.

    Args:
      emdocument_class: The EmDocument child class.
      Everything else are inheritted from BaseProperty
    """
    BaseProperty.__init__(self, **args)
    self.emdocument_class = emdocument_class
    if self._default is _NOUNCE:
      self._default = lambda: []

  def validate(self, value):
    if not BaseProperty.validate(self, value):
      return False

    for d in value:
      if d is not None and (not isinstance(d, self.emdocument_class) or not d.is_valid()):
        return False

    return True

  def to_db(self, value):
    return [None if d is None else d.serialize() for d in value] if value else None

  def from_db(self, value):
    return [None if d is None else self.emdocument_class.load(d) for d in value] if value else None

class ReferenceProperty(BaseProperty):
  """Reference property references another Document.

  Stores the key of the other class in the db and retrieves on demand.
  Probably shouldn't even use this as index is better in most scenarios.
  """

  def __init__(self, reference_class, strict=False, **kwargs):
    """Initializes a new ReferenceProperty

    Args:
      reference_class: The Document child class that this property is
          referring to.
      strict: If True and if the object is not found in the database
          loading it, it will raise a NotFoundError. If load_on_demand
          is False and it tries to load this property with a
          non-existent object, it will also raise a NotFoundError.
    """
    BaseProperty.__init__(self, **kwargs)
    if not hasattr(reference_class, "get"):
      raise ValueError("ReferenceProperty only accepts Document based classes (offender: {0}).".format(reference_class.__class__))
    self.reference_class = reference_class
    self.strict = strict

  def validate(self, value):
    return BaseProperty.validate(self, value) and \
           (value is None or isinstance(value, self.reference_class))

  def to_db(self, value):
    if value is None or isinstance(value, basestring):
      return value

    return value.key

  def from_db(self, value):
    if value is None:
      return None

    try:
      doc = self.reference_class.get(value)
    except NotFoundError, e:
      if self.strict:
        raise e
    return doc
