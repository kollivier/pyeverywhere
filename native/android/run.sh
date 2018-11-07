SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DIR=$PWD/native/android

cd "$DIR"

echo "PWD is $PWD"

adb start-server
adb install -r $1
adb shell "am start -a android.intent.action.MAIN -n $2/org.kivy.android.PythonActivity"
adb logcat PythonActivity:V python:D BatteryService:S Sensors:S SensorService:S WifiAutoJoinController:S WifiTrafficPoller:S WifiAutoJoinController:S WifiStateMachine:S NetworkController:S WifiConfigStore:S AudioPolicyManagerALSA:S NowDoodleController:S chromium:I *:E 
