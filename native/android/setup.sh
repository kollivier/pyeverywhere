DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

export ANDROIDSDK="$DIR/sdk"
export ANDROIDNDK="$DIR/android-ndk-r10b"
export ANDROIDNDKVER=r10b
export ANDROIDAPI=19

export ANT_HOME="$DIR/apache-ant-1.9.4"
echo "Android NDK is $ANDROIDNDK"


export PATH=$ANDROIDNDK:$ANDROIDSDK/platform-tools:$ANDROIDSDK/tools:$ANT_HOME/bin:$PATH
