#!/bin/bash

START_DIR=$PWD
DIR=${ANDROID_ROOT}
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

echo "Dir is $DIR"
echo "Script Dir is $SCRIPT_DIR"
if [ ! -d $DIR ]
then
    mkdir -p "$DIR"
fi

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo Platform is $PLATFORM

export ANDROID_HOME=$DIR/android-sdk-$PLATFORM
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

FORMAT=tgz
if [[ "$PLATFORM" == "macosx" ]]; then
    FORMAT=zip
fi

echo Downloading http://dl.google.com/android/android-sdk_r24.4.1-$PLATFORM.$FORMAT

if [ ! -d android-sdk-$PLATFORM ] 
then
    curl --location http://dl.google.com/android/android-sdk_r24.4.1-$PLATFORM.$FORMAT | tar -x -z -C .
fi 

android update sdk --no-ui --all --filter platform-tool,android-$ANDROIDAPI,sysimg-$ANDROIDAPI,build-tools-$ANDROIDBUILDTOOLSVER

if [ ! -d android-ndk-$ANDROIDNDKVER ]
then
    curl -o android-ndk.bin --location http://dl.google.com/android/ndk/android-ndk-$ANDROIDNDKVER-$NDKPLATFORM-x86_64.bin
    chmod a+x android-ndk.bin
    ./android-ndk.bin
fi 

echo Downloading https://archive.apache.org/dist/ant/binaries/apache-ant-$ANT_VERSION-bin.tar.gz

if [ ! -d apache-ant-$ANT_VERSION ]
then
    curl --location https://archive.apache.org/dist/ant/binaries/apache-ant-$ANT_VERSION-bin.tar.gz | tar -x -z -C .
fi
