SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DIR=$PWD/native/android

. $SCRIPT_DIR/setup.sh

cd "$DIR"

echo "PWD is $PWD"

adb kill-server; adb start-server
adb install -r $1
adb shell "am start -a android.intent.action.MAIN -n $2/org.renpy.android.PythonActivity"
adb logcat python:D *:I