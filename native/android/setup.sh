#DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT_DIR="$PWD/native/android"

export ANT_VERSION="1.9.6"

export ANDROIDSDK="$ROOT_DIR/android-sdk-macosx"
export ANDROIDNDKVER=r10e
export ANDROIDNDK="$ROOT_DIR/android-ndk-$ANDROIDNDKVER"
export ANDROIDAPI=19
export ANDROIDBUILDTOOLSVER=19.1.0

export ANT_HOME="$ROOT_DIR/apache-ant-$ANT_VERSION"
echo "Android NDK is $ANDROIDNDK"


export PATH=$ANDROIDNDK:$ANDROIDSDK/platform-tools:$ANDROIDSDK/tools:$ANT_HOME/bin:$PATH
