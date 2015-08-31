SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DIR=$PWD/native/android

. $SCRIPT_DIR/setup.sh


cd "$DIR"

echo "PWD is $PWD"

cd python-for-android
./distribute.sh -m "kivy pyjnius django pil ffmpeg openssl sqlite3"