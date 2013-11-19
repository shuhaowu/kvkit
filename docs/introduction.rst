.. _introduction-chapter:

=====================
Introduction to KVKit
=====================

Simple Tutorial
---------------

KVKit is a natural extension to JSON based document stores. It naturally
serve as your model layer.

Using the API is simple. Here's a simple example with a blog::

    >>> from kvkit import *
    >>> from kvkit.backends import slow_memory
    >>> class BlogPost(Document):
    ...     # _backend is required
    ...     _backend = slow_memory
    ...
    ...     title = StringProperty(required=True) # StringProperty auto converts all strings to unicode
    ...     content = StringProperty() # let's say content is not required.
    ...     some_cool_attribute = NumberProperty() # Just a random attribute for demo purpose
    ...
    ...     def __str__(self): # Totally optional..
    ...         return "%s:%s" % (self.title, self.content)

We can create and save a document::

    >>> post = BlogPost(data={"title": "hi"})
    >>> print post
    hi:None
    >>> post.save() # Note since we are using the slow_memory backend, this is not actually saved.
    <__main__.BlogPost object at ...>

Modifying the document is easy too::

    >>> post.title = "Hello"
    >>> post.content = "mrrow"
    >>> post.save()
    <__main__.BlogPost object at ...>
    >>> print post
    Hello:mrrow
    >>> key = post.key # The key.

Since title is required, trying to save an object without a title won't work::

    >>> another_post = BlogPost(data={"content": "lolol"})
    >>> another_post.save()
    Traceback (most recent call last):
        ...
    ValidationError: ...

We can also try getting some stuff from the db::

    >>> same_post = BlogPost.get(key) # this is the key from before
    >>> print same_post
    Hello:mrrow

If your data is modified somehow, you need to reload::

    >>> same_post.reload() # Obviously we haven't changed anything, but if we did, this would get those changes
    >>> print same_post.title
    Hello

You can also use dictionary notation::

    >>> print same_post.title
    Hello
    >>> print same_post["title"]
    Hello

You can have attributes not in your schema::

    >>> same_post.random_attr = 42
    >>> same_post.save()
    <__main__.BlogPost object at ...>
    >>> print same_post.random_attr
    42

Accessing non-existent attributes will fail::

    >>> same_post.none_existent
    Traceback (most recent call last):
      ...
    AttributeError: ...

Accessing a non-existent attribute that's **in** your schema will return
``None``::

    >> print same_post.some_cool_attribute  # Remember? We never set this
    None

You can also delete stuff::

    >>> same_post.delete()
    >>> BlogPost.get(key)
    Traceback (most recent call last):
        ...
    NotFoundError: ...

Indexes
-------

Backends that support indexes can retrieve data not just via the key, but also
some field and values. Here are some examples::


    class BlogPost(Document):
      _backend = slow_memory

      title = StringProperty(required=True)
      tags = ListProperty(index=True)
      # Let's say we just store a lowercase username
      author = StringProperty(index=True)


    post = BlogPost(data={"title": "hello world", "tags": ["hello", "world"], "author": "john"})
    post.save()

That just created a post with index and saved the index in whatever the backend
prefers. The slow_memory backend doesn't as index operation just iterates
through. This is why you shouldn't be using it.

To query indexed data, there are two ways: getting an object, or just get the
primary keys::

    # Get the indexed object. Returns an iterator
    for post in BlogPost.index("tags", "hello"):
      # prints hello world once.
      print post.title

    # Get the keys only.
    # Prints [post.key]
    print BlogPost.index_keys_only("tags", "hello")

You can also query for a range::

    # low <= value <= high
    for post in BlogPost.index("tags", "h", "i"):
      # prints hello world once
      print post.title

Fancy Properties
----------------

JSON documents can really contain anything right? This is absolutely true, but
it might still be helpful to use KVKit's properties to define your documents as
different backends might have optimizations for different properties.

There are plenty of properties available from the built in
that does a lot of different things. For more details you can take a look at
the API docs' properties section. However, there are some patterns that we
should follow.

By default, kvkit deserializes values into their corresponding python objects
on load. Occasionally, this could be slow, such as in the case of a
``ReferenceProperty``. When an object with a ``ReferenceProperty`` loads,
by default, it will automatically load the referenced object, and cascade down
the tree in a depth first fashion. This could be really bad.

To avoid this, all property initialization takes an optional argument called
``load_on_demand``. This moves deserialization when the value is *accessed*.

To illustrate this::

    class ReferencedDocument(Document):
      _backend = slow_memory

    class SomeDocument(Document):
      _backend = slow_memory

      ref = ReferenceProperty(ReferencedDocument, load_on_demand=True)

    refdoc = ReferencedDocument()
    somedoc = SomeDocument(data={"ref": refdoc})
    refdoc.save() # No magic here. You need to save this document first.
    somedoc.save()

    d = SomeDocument.get(somedoc.key)
    print d.ref.key == refdoc.key # True

Note ``d.ref`` is not actually loaded when you perform the get operation. It is
done when you access it and cached there. This is when you should be careful
with race conditions as any changes with ``refdoc`` will not be immediately
reflected by ``d.ref`` until the next reload!

Property Validators
-------------------

KVKit provides a way to validate data on save, as well as some convenience
methods for checking for validity or which field is invalid. In effect, it
could in theory replace your forms library if you don't need things that are
too complicated.

Here's an example::

    class ValidatedDoc(Document):
        _backend = slow_memory

        required = StringProperty(required=True)
        integer = NumberProperty(validators=lambda x: abs(int(x) - x) < 0.00001)

    vdoc = ValidatedDoc()

    # Check if document is valid
    print vdoc.is_valid() # false

    # Check which fields are invalid
    print vdoc.invalids() # ["required"]

Note that only ``required`` is considered to be invalid as ``integer`` is
not required and accepted as valid.

If we are to do this::

    vdoc.integer = 1.5
    print vdoc.invalids() # ["integer", "required"]

Note that calling ``invalids`` is slightly less efficient than ``is_valid`` as
``is_valid`` quits on the first validation error.

You will not be allowed to save a document with validation error::

    vdoc.save() # Raises ValidationError

There's another convenience feature for KVKit that disallows extra attributes
for the document::

    class OnlyDefined(Document):
        _backend = slow_memory
        DEFINED_PROPERTIES_ONLY = True

        a = StringProperty()

    odoc = OnlyDefined()
    odoc.b = "yay"
    print odoc.invalids() # ["_extra_prop"]

Note the invalids returns a special ``_extra_prop`` as a hint saying that
there is extra properties.

This is good if you doing something like ``Document(data=request.forms)``.

Embedded Documents
------------------


