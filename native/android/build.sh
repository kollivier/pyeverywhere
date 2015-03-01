START_DIR=$PWD
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd $DIR

echo "PWD is $PWD"

. setup.sh

cp $PWD/src/org/kosoftworks/pyeverywhere/*.java $DIR/python-for-android/dist/default/src

cd $DIR/python-for-android/dist/default
python build.py --package $1 --name $2 --version $3 --permission INTERNET --permission WRITE_EXTERNAL_STORAGE --dir $4 debug

mkdir -p $START_DIR/dist/android
echo "cp bin/$2-$3*.apk $START_DIR/dist/android"
cp bin/$2-$3*.apk $START_DIR/dist/android