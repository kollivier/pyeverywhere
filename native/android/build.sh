START_DIR=$PWD
DIR=$PWD/native/android
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo "PWD is $PWD"

cp $SCRIPT_DIR/src/org/kosoftworks/pyeverywhere/*.java $DIR/python-for-android/dist/default/src

cd python-for-android/dist/default
python build.py --package $1 --name $2 --version $3 --orientation fullUser --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --dir $4 debug

mkdir -p $START_DIR/dist/android
if [ ! -d bin ]
then
    mkdir bin
fi

echo "cp bin/$2-$3*.apk $START_DIR/dist/android"
cp bin/$2-$3*.apk $START_DIR/dist/android