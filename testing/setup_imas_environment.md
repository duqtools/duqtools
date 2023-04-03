# Instructions for compiling imas on your machine

This sets up IMAS using your python environment.

## Requirements

    sudo apt-get install -y xsltproc cmake default-jdk

## Clone DD/AL repos

    git clone https://$USERNAME@git.iter.org/scm/imas/data-dictionary.git imas/data-dictionary
    git clone --depth=1 https://$USERNAME@git.iter.org/scm/imas/access-layer.git imas/access-layer

## Get saxon

    mkdir saxon9he
    cd saxon9he
    curl -L https://sourceforge.net/projects/saxon/files/Saxon-HE/9.9/    SaxonHE9-9-1-7J.zip/download -o saxon9he.zip
    unzip saxon9he.zip

## Compile and install blitz

    git clone https://github.com/blitzpp/blitz
    cd blitz
    mkdir build
    cd build
    cmake -DCMAKE_INSTALL_PREFIX=../local/ ..
    make lib
    make install
    cd ../..

## Setup python environment with pip

    python -m virtualenv .venv
    . .venv/bin/activate

## Compile and install imas

    cd imas
    mv ../saxon9he/saxon9he.jar .
    ln -s ../testing/build_imas_script.sh .
    . build_imas_script.sh
    cd ..

## Set up imas next time

    . ./imas/source_me.sh
