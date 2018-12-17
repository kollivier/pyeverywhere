START_DIR=$PWD
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

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

REQUIREMENTS="--requirements=python2,pyjnius,genericndkbuild"
if [ ! -z $9 ]
then
REQUIREMENTS="--requirements=$9"
fi

BUILD_TYPE=
if [ ! -z "${10}" ]
then
BUILD_TYPE="--release"
fi

INTENT_FILTERS=
if [ ! -z "${11}" ]
then
INTENT_FILTERS="--intent-filters ${11}"
fi

if [ ! -z "${12}" ]
then
echo "Keystore is ${12}"
echo "keyalias is ${13}"
KEYINFO="--keystore ${12} --signkey ${13} --keystorepw ${14}"
fi

BLACKLIST=
if [ ! -z "${15}" ]
then
  BLACKLIST="--blacklist ${15}"
fi

LAUNCH_BG="--presplash-color white"
if [ ! -z "${16}" ]
then
  LAUNCH_BG="--presplash-color ${16}"
fi

DIST_DIR="$HOME/.local/share/python-for-android/dists"
if [ "$(uname)" == "Darwin" ]; then
    DIST_DIR="$HOME/.python-for-android/dists"
fi

echo "Packaging files"

p4a apk --private=$4 --window $REQUIREMENTS $BUILD_TYPE --package=$1 --name=$2 --dist_name="${DIST_NAME}" --version=$3 --permission=INTERNET --permission=WRITE_EXTERNAL_STORAGE --bootstrap=webview $ICON $WHITELIST $ORIENTATION $LAUNCH $INTENT_FILTERS --add-source=$SCRIPT_DIR/src/org/kosoftworks/pyeverywhere $KEYINFO $BLACKLIST $LAUNCH_BG

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

cp "${DIST_DIR}/${DIST_NAME}"/bin/$2-$3*.apk "${START_DIR}"/dist/android
