import os
print(os.popen("/home/young/Android/Sdk//platform-tools/adb shell sendevent /dev/input/event1 1 330 1").read())