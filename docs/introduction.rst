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



