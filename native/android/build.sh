START_DIR=$PWD
DIR=$PWD/native/android
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo "PWD is $PWD"

DIST_NAME="$2_dist"

ICON=
if [ -f $5 ]
then
ICON="--icon $5"
fi

LAUNCH=
if [ -f $6 ]
then
LAUNCH="--presplash $6"

fi

WHITELIST=
if [ -f $7 ]
then
WHITELIST="--whitelist $7"
fi

ORIENTATION="--orientation sensor"
if [ ! -z $8 ]
then
ORIENTATION="--orientation $8"
fi

REQUIREMENTS="--requirements=python2,kivy,pyjnius,android"
if [ ! -z $9 ]
then
REQUIREMENTS="--requirements=$9"
fi

BUILD_TYPE=
if [ ! -z "${10}" ]
then
BUILD_TYPE="--release"
fi

if [ ! -z "${11}" ]
then
echo "Keystore is ${11}"
echo "keyalias is ${12}"
KEYINFO="--keystore ${11} --signkey ${12} --keystorepw ${13}"
fi

DIST_DIR="$HOME/.local/share/python-for-android/dists"
if [ "$(uname)" == "Darwin" ]; then
    DIST_DIR="$HOME/.python-for-android/dists"
fi

p4a apk --private=$4 $REQUIREMENTS $BUILD_TYPE --package=$1 --name=$2 --dist_name="${DIST_NAME}" --version=$3 --permission=INTERNET --permission=WRITE_EXTERNAL_STORAGE --bootstrap=sdl2 $ICON $WHITELIST $ORIENTATION $LAUNCH --add-source=$SCRIPT_DIR/src/org/kosoftworks/pyeverywhere $KEYINFO

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

cp "${DIST_DIR}/${DIST_NAME}"/bin/$2-$3*.apk "${START_DIR}"/dist/android
