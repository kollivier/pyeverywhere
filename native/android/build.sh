START_DIR=$PWD
DIR=$PWD/native/android
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo "PWD is $PWD"

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

cd src

p4a apk --private=$4 --requirements=python2,kivy,pyjnius,openssl,android --package=$1 --name=$2 --version=$3 --orientation sensor --permission=INTERNET --permission=WRITE_EXTERNAL_STORAGE --bootstrap=sdl2 $ICON --add-source=$SCRIPT_DIR/src/org/kosoftworks/pyeverywhere

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

echo "cp bin/$2-$3*.apk $START_DIR/dist/android"
echo cp bin/$2-$3*.apk $START_DIR/dist/android
