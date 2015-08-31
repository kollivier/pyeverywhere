START_DIR=$PWD
DIR=$PWD/native/android
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

echo "Dir is $DIR"
if [ ! -d $DIR ]
then
    mkdir -p "$DIR"
fi

. $SCRIPT_DIR/setup.sh

cd "$DIR"

PLATFORM='linux'
NDKPLATFORM='linux'
unamestr=`uname`
if [[ "$unamestr" == 'Darwin' ]]; then
   PLATFORM='macosx'
   NDKPLATFORM='darwin'
fi

echo Platform is $PLATFORM

export ANDROID_HOME=$DIR/android-sdk-$PLATFORM
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
    
if [ ! -d android-sdk-macosx ] 
then
    curl --location http://dl.google.com/android/android-sdk_r24.3.4-$PLATFORM.zip | tar -x -z -C .
fi 

android update sdk --no-ui --all --filter platform-tool,android-$ANDROIDAPI,sysimg-$ANDROIDAPI,build-tools-$ANDROIDBUILDTOOLSVER

if [ ! -d android-ndk-$ANDROIDNDKVER ]
then
    curl -o android-ndk.bin --location http://dl.google.com/android/ndk/android-ndk-$ANDROIDNDKVER-$NDKPLATFORM-x86_64.bin
    chmod a+x android-ndk.bin
    ./android-ndk.bin
fi 

if [ ! -d apache-ant-$ANT_VERSION ]
then
    curl --location http://www.trieuvan.com/apache/ant/binaries/apache-ant-$ANT_VERSION-bin.tar.gz | tar -x -z -C .
fi

if [ ! -d python-for-android ]
then
    git clone https://github.com/kivy/python-for-android.git
fi