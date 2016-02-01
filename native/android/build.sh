START_DIR=$PWD
DIR=$PWD/native/android
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo "PWD is $PWD"

cp $SCRIPT_DIR/src/org/kosoftworks/pyeverywhere/*.java $DIR/python-for-android/dist/default/src

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

cd python-for-android/dist/default
echo "build.py --package $1 --name $2 --version $3 --orientation landscape --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --dir $4 $ICON debug
"
python build.py --package $1 --name $2 --version $3 --orientation landscape --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --dir $4 $ICON $LAUNCH debug

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

echo "cp bin/$2-$3*.apk $START_DIR/dist/android"
cp bin/$2-$3*.apk $START_DIR/dist/android