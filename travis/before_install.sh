#!/bin/bash

# Setup travis
sudo dpkg -i travis/riak*.deb
sudo riak stop
sudo cp travis/app.config /etc/riak/app.config
sudo riak start

pushd travis
  tar xvf leveldb-1*
  pushd leveldb*
    make
    sudo cp --preserve=links libleveldb.* /usr/local/lib
    sudo cp -r include/leveldb /usr/local/include/
    sudo ldconfig
  popd
popd

mkdir -p dbs
