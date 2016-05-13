#!/bin/bash

START_DIR=$PWD
DIR=$PWD/native/android
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

echo Downloading http://mirrors.sonic.net/apache/ant/binaries/apache-ant-$ANT_VERSION-bin.tar.gz

if [ ! -d apache-ant-$ANT_VERSION ]
then
    curl --location http://mirrors.sonic.net/apache/ant/binaries/apache-ant-$ANT_VERSION-bin.tar.gz | tar -x -z -C .
fi

if [ ! -d python-for-android ]
then
    pip install --upgrade --force-reinstall git+https://github.com/kivy/python-for-android.git
fi
