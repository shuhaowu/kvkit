from distutils.core import setup

setup(
    name="kvkit",
    version="0.1.0",
    packages=["kvkit"],
    description="KVKit is an object mapper for key value stores (NoSQL). It supports multiple backends such as Riak and LevelDB.",
    author="Shuhao Wu",
    author_email="shuhao@shuhaowu.com",
    url="https://github.com/shuhaowu/kvkit",
    license="LGPL",
    keywords="riak object mapper kvkit database nosql orm leveldb",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)