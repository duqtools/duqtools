#!/bin/bash

# Derived from
# https://git.iter.org/projects/IMAS/repos/imaspy/browse/envs/common/25_build_imas_git.sh
set -e

export CLASSPATH=`pwd`/../saxon9he/saxon9he.jar

cd data-dictionary
# use the latest tagged version
export IMAS_VERSION=`git tag | sort -V | tail -n 1`
git checkout "$IMAS_VERSION"
make


cd ..
cd access-layer
if [ ! -L xml ]; then
    ln -s ../data-dictionary/ xml
fi

export UAL_VERSION=`git tag | sort -V | tail -n 1`
export IMAS_UDA=no \
    IMAS_MDSPLUS=yes \
    IMAS_HDF5=yes \
    IMAS_MATLAB=no \
    IMAS_MEX=no \
    IMAS_JAVA=no

export IMAS_PREFIX=`pwd`
export LIBRARY_PATH=`pwd`/lowlevel:${LIBRARY_PATH:=}
export C_INCLUDE_PATH=`pwd`/lowlevel:${C_INCLUDE_PATH:=}
# Hard patch hdf5 to the correct directories
export CPLUS_INCLUDE_PATH=`pkg-config hdf5-serial --cflags | cut -dI -f2`:${CPLUS_INCLUDE_PATH}
export CPLUS_INCLUDE_PATH=/usr/local/mdsplus/include:${CPLUS_INCLUDE_PATH}
export LD_LIBRARY_PATH=`pwd`/lowlevel:`pwd`/cppinterface/lib:${LD_LIBRARY_PATH:=}
export LIBRARY_PATH=`pkg-config hdf5-serial --libs-only-L | cut -dL -f2`:${LIBRARY_PATH}
export LIBRARY_PATH=`pkg-config boost --libs-only-L | cut -dL -f2`:${LIBRARY_PATH}
export LIBRARY_PATH=/usr/local/mdsplus/lib:${LIBRARY_PATH}

cd lowlevel
make -j `nproc`
cd ..

pip install numpy cython

cd pythoninterface
make -j`nproc`
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# We do not always start from a cleaned virtual environment.
# Uninstall possible leftover packages
pip uninstall --yes imas || true

pip install -e package

cd ../../

rm source_me.sh
echo "export UAL_VERSION=$UAL_VERSION" >> source_me.sh
echo "export IMAS_PREFIX=$IMAS_PREFIX" >> source_me.sh
echo "export LIBRARY_PATH=$LIBRARY_PATH" >> source_me.sh
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH" >> source_me.sh

# Usage: `. source_me.sh`
