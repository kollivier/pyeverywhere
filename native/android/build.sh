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

DIST_DIR="$HOME/.local/share/python-for-android/dists"
if [ "$(uname)" == "Darwin" ]; then
    DIST_DIR="$HOME/.python-for-android/dists"
fi

cd src

p4a clean_dists
p4a apk --private=$4 --requirements=python2,kivy,pyjnius,android,sqlite3 --package=$1 --name=$2 --dist_name="${DIST_NAME}" --version=$3 --permission=INTERNET --permission=WRITE_EXTERNAL_STORAGE --bootstrap=sdl2 $ICON $WHITELIST $ORIENTATION --add-source=$SCRIPT_DIR/src/org/kosoftworks/pyeverywhere

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

cp "${DIST_DIR}/${DIST_NAME}"/bin/$2-$3*.apk "${START_DIR}"/dist/android
