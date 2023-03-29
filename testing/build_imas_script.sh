#!/bin/bash

# Build a copy of IMAS components need by IMASPy from the access-layer monorepo and
# data-dictionary repo. You can specify the AL version with $1 (usually "develop" or "master")
# The DDs will be scanned by IMASPy anyway, but we'll build the default branch as well

# # Script boilerplate
# [[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

# common_dir=$my_dir
# . $common_dir/00_common_bash.sh

# old_bash_state="$(get_bash_state "$old_bash_state")"
# set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

export CLASSPATH=`pwd`/saxon9he.jar

cd data-dictionary
# use the latest tagged version
export IMAS_VERSION=`git tag | sort -V | tail -n 1`
git checkout "$IMAS_VERSION"
make

cd ..
# INSTALL the access layer locally (this might take a while)
cd access-layer
if [ ! -L xml ]; then
    ln -s ../data-dictionary/ xml
fi

export UAL_VERSION=`git tag | sort -V | tail -n 1`
export IMAS_UDA=no \
    IMAS_MDSPLUS=no \
    IMAS_HDF5=no \
    IMAS_MATLAB=no \
    IMAS_MEX=no \
    IMAS_JAVA=no

export IMAS_PREFIX=`pwd`
export LIBRARY_PATH=`pwd`/lowlevel:${LIBRARY_PATH:=}
export C_INCLUDE_PATH=`pwd`/lowlevel:${C_INCLUDE_PATH:=}
export LD_LIBRARY_PATH=`pwd`/lowlevel:`pwd`/cppinterface/lib:${LD_LIBRARY_PATH:=}

cd lowlevel
make -j`nproc`
cd ..

pip install numpy cython

cd pythoninterface
make -j`nproc`
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# We do not always start from a cleaned virtual environment. Uninstall possible leftover packages
pip uninstall --yes imas || true

# Install locally
pip install -e package

# test if we can import the imas module
python -c 'import imas'

cd ../../

echo "export UAL_VERSION=$UAL_VERSION" >> source_me.sh
echo "export IMAS_PREFIX=$IMAS_PREFIX" >> source_me.sh
echo "export LIBRARY_PATH=$LIBRARY_PATH" >> source_me.sh
echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH" >> source_me.sh
