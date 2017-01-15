#!/bin/bash

ROOT_DIR="$PWD/native/android"

echo "$ROOT_DIR/setup.sh"
. $ROOT_DIR/setup.sh

export ANT_VERSION="1.9.8"

PLATFORM='linux'
NDKPLATFORM='linux'
unamestr=`uname`
if [[ "$unamestr" == "Darwin" ]]; then
   PLATFORM='macosx'
   NDKPLATFORM='darwin'
fi

export ANDROIDSDK="$ROOT_DIR/android-sdk-$PLATFORM"
export ANDROIDNDKVER=r10e
export ANDROIDNDK="$ROOT_DIR/android-ndk-$ANDROIDNDKVER"

export ANT_HOME="$ROOT_DIR/apache-ant-$ANT_VERSION"
echo "Android NDK is $ANDROIDNDK"

export PATH=$ANDROIDNDK:~/.local/bin:$ANDROIDSDK/platform-tools:$ANDROIDSDK/tools:$ANT_HOME/bin:$PATH
