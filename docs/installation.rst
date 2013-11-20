.. _installation-chapter:

============
Installation
============

To install this, simply install from pip::

    $ pip install kvkit

By default, this installation does not come with any backends other than the
``slow_memory`` backend, which you should not use.

If you need to use the riak backend, you need to install the riak pip package
as well::

    $ pip install riak

If you need to use the leveldb backend, you need to install.. TBD.

    $ # TBD

For development of kvkit, start a new virtualenv and do:

    $ pip install -r requirements.txt
