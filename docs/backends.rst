.. _backend-chapter:

========
Backends
========

KVKit uses backends to support multiple backend databases. The current
supported ones includes: Riak, LevelDB, and a very slow memory
implementation for testing.

Using Backends
--------------

Each class has an attribute called ``_backend``. This needs to be set to an
appropriate backend.

To use a backend that's built in, import from ``kvkit.backends``::

    from kvkit.backends import riak

    class YourDocument(Document):
        _backend = riak

        # ...

If you use the same backend all the time, you can define a base class::

    from kvkit.backends import riak

    class BaseDocument(Document):
        _backend = riak

    class YourDocument(BaseDocument):
        # ... your attributes

If your have your own custom backend, you can use that. The current available
backends are detailed below.

Riak Backend
------------

``kvkit.backends.riak``

.. automodule:: kvkit.backends.riak
    :members:

LevelDB Backend
---------------

``kvkit.backends.leveldb``

.. automodule:: kvkit.backends.leveldb
    :members:

Slow Memory Backend
-------------------

``kvkit.backends.slow_memory``

.. automodule:: kvkit.backends.slow_memory
    :members:

Writing Backends
----------------

There are two approaches in writing a backend. You can either

- start with a module and fill in all the functions listed below,
  import the module and set it as the backend.
- inherit the class, and then fill in the appropriate functions,
  import the class, initialize it, and set it as the backend.

Make sure you stick to the format specified in the docs below or else it
won't work. Feel free to ``raise NotImplementedError`` if your backend does
not support the operations.

Base Backend API Documentations for Implementation
--------------------------------------------------

This is mostly for writing the backends. When you actually use kvkit,
``Document`` hides all these nonsense from you.

.. automodule:: kvkit.backends.base
    :members:
    :undoc-members:
