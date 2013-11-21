kvkit
=====

**kvkit** is an object mapper and a RAD tool for key value stores.

Currently, supported backends include:

  - leveldb
  - riak

This project serves as a replacement for [riakkit][rk] and [leveldbkit][lk].

[rk]: https://github.com/shuhaowu/riakkit
[lk]: https://github.com/shuhaowu/leveldbkit

If you have used riakkit in the past, you may have noticed missing features.
This is intentional and those features will not come back due to their
performance/code quality implications.

kvkit uses a modular design that makes it easily portable to other storage
backends. Backends can be found in `backends/`. A starting point is by copying
base.py (either the module functions or the class). `slow_memory` is a good
example implementation of the database in memory that is used in tests.

[![Travis Build
Status](https://travis-ci.org/shuhaowu/kvkit.png)](https://travis-ci.org/shuhaowu/kvkit.png)

Documentations available at http://kvkit.readthedocs.org/.
