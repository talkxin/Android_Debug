import os
import time
import threading
import pexpect
import re
import src.AndroidKeyName
import copy

# android目录
ANDROID_HOME = ""
# adb路径
_adb = ""
_Recording = True
# 是否录制
recording = True
# 触摸精度
Event_Precision = 10
userEvent = []
class Key():
        keytime = None
        keyevent = None
        keytype = None
        keyname = None
        keycode = None
        keyend = False
# class 处理adb各种数据
class AdbService(threading.Thread):
    # 用于处理提取event事件的正则表达式
    keyre = re.compile(".*?([+-]?\\d*\\.\\d+)(?![-+0-9\\.]).*?((?:\\/[\\w\\.\\-]+)+).*?(\\d+).*?((?:[a-z0-9][a-z0-9]*[a-z0-9]+[a-z0-9]*)).*?((?:[a-z0-9][a-z0-9]*[a-z0-9]+[a-z0-9]*))", re.IGNORECASE | re.DOTALL)
    # 触摸屏的x与y的最大与最小,用于坐标转换
    xMax = None
    xMin = None
    yMax = None
    yMin = None
    # 屏幕的分辨率,用于坐标转换
    k_Hight = None
    k_Width = None
    # x,y坐标,若x或y不变则不会继续传值
    valX = 0
    valY = 0
    # 触摸事件head
    __teach = None
    # 触摸x
    __teach_x = None
    # 触摸y
    __teach_y = None
    def __init__(self):
        super().__init__()
        # 初始化触摸屏的xy与坐标的分辨率
        self.initCoordinate()
        self.initResolution()
    # 获取屏幕的xy值的相对值
    def initCoordinate(self):
        command = os.popen("%s shell getevent -p" % (_adb)).read().splitlines()
        minre = re.compile('.*?(min)(.)(\\d+)', re.IGNORECASE | re.DOTALL)
        maxre = re.compile('.*?(max)(.)(\\d+)', re.IGNORECASE | re.DOTALL)
        for d in range(0, len(command) - 1):
            n = minre.search(command[d])
            m = maxre.search(command[d])
            if(n and m):
                keyname = int(re.compile(".*? .*? .*? .*? .*? .*?( )((?:[a-z0-9][a-z0-9]*[a-z0-9]+[a-z0-9]*))(  )", re.IGNORECASE | re.DOTALL).search(command[d]).group(2), 16)
                if(src.AndroidKeyName.KEYNAME_TEACH_X == keyname):
                    self.xMax = int(m.group(3), 10)
                    self.xMin = int(n.group(3), 10)
                elif(src.AndroidKeyName.KEYNAME_TEACH_Y == keyname):
                    self.yMax = int(m.group(3), 10)
                    self.yMin = int(n.group(3), 10)
    # 获取屏幕的分辨率
    def initResolution(self):
        command = os.popen('''%s  shell dumpsys window |grep "ShownFrame"|grep "HasSurface=true"|head -n 1''' % (_adb)).read().splitlines()
        m = re.compile(".*?\\[.*?(\\[)([+-]?\\d*\\.\\d+)(?![-+0-9\\.])(,)([+-]?\\d*\\.\\d+)(?![-+0-9\\.])(\\])", re.IGNORECASE | re.DOTALL).search(command[0])
        if(m):
            self.k_Width = float(m.group(2))
            self.k_Hight = float(m.group(4))
    # 提取事件与数值进行返回
    def eventCode(self, cmd):
        key = self.keyre.search(cmd)
        if (key):
            try:
                keyname = int(key.group(4), 16)
                keycode = int(key.group(5), 16)
                return keyname, keycode
            except ValueError:
                return None, None
        else:
            return None, None
    # 返回所有键值数据
    def eventAllCade(self, cmd):
        key = self.keyre.search(cmd)
        if(key):
            try:
                keytime = float(key.group(1))
                keyevent = key.group(2)
                keytype = int(key.group(3), 16)
                keyname = int(key.group(4), 16)
                keycode = int(key.group(5), 16)
                return keytime, keyevent, keytype, keyname, keycode
            except ValueError:
                return None, None, None, None, None
        else:
            return None, None, None, None, None
    # xy坐标转换
    def eventXY2xy(self, origin, n):
        if(n == src.AndroidKeyName.KEYNAME_TEACH_X):
            return format((origin - self.xMin) * self.k_Width / (self.xMax - self.xMin), '.2f')
        elif(n == src.AndroidKeyName.KEYNAME_TEACH_Y):
            return (format((origin - self.yMin) * self.k_Hight / (self.yMax - self.yMin), '.2f'))
    def run(self):
        child = pexpect.spawn("%s shell getevent -t" % (_adb), timeout=None)
        while _Recording:
            # 上一组指令的时间
            child.expect (["\r\n", "\r\x1b", "\r"], timeout=None)
            cmd = child.before.decode()
            k = Key()
            k.keytime, k.keyevent, k.keytype, k.keyname, k.keycode = self.eventAllCade(cmd)
            if(k.keytime != None and _Recording):
                if(k.keyname == src.AndroidKeyName.KEYNAME_TEACH_EVENT and k.keycode == 1):
                    self.__teach = k.keytime
                    # 录入触摸起始位置
                    userEvent.append(k)
                elif(k.keyname == src.AndroidKeyName.KEYNAME_TEACH_EVENT and k.keycode == 0):
                    self.__teach = None
                    self.__teach_x = None
                    self.__teach_y = None
                    # 录入触摸终点位置
                    userEvent.append(k)
                    # 记录操作终止符
                    end = copy.deepcopy(k)
                    end.keytype = 0
                    end.keyname = 0
                    end.keycode = 0
                    end.keyend = True
                    userEvent.append(end)
                    
                # 录制end符
                if(k.keyname == src.AndroidKeyName.KEYNAME_THACHEND and len(userEvent) != 0 and userEvent[len(userEvent) - 1].keyname != src.AndroidKeyName.KEYNAME_THACHEND):
                        userEvent.append(k)
                # 判断属于一个触摸事件段
                if(self.__teach != None):
                    if(k.keyname == src.AndroidKeyName.KEYNAME_TEACH_X):
                        if(self.__teach_x != None):
                            precision = k.keycode - self.__teach_x
                            precision = precision > 0 and precision or precision * -1
                            if(precision > Event_Precision):
                                userEvent.append(k)
                                self.__teach_x = k.keycode
                        else:
                            userEvent.append(k)
                            self.__teach_x = k.keycode
                    if(k.keyname == src.AndroidKeyName.KEYNAME_TEACH_Y):
                        if(self.__teach_y != None):
                            precision = k.keycode - self.__teach_y
                            precision = precision > 0 and precision or precision * -1
                            if(precision > Event_Precision):
                                userEvent.append(k)
                                self.__teach_y = k.keycode
                        else:
                            userEvent.append(k)
                            self.__teach_y = k.keycode
#                         userEvent[self.__teach].append("%s shell sendevent %s %d %d %d" % (_adb, keyevent, keytype, keyname, keycode))

class UserPlay():
    def play(self):
        for i in range(0, len(userEvent)):
            event = userEvent[i]
            os.system("%s shell sendevent %s %d %d %d" % (_adb, event.keyevent, event.keytype, event.keyname, event.keycode))
            if(event.keyend and i < len(userEvent) - 1):
                enext = userEvent[i + 1]
                print(enext.keytime - event.keytime)
                time.sleep(enext.keytime - event.keytime)

if(os.getenv("ANDROID_HOME") != None):
    ANDROID_HOME = os.getenv("ANDROID_HOME")
    # 找到adb路径
    _adb = ANDROID_HOME + "/platform-tools/adb"
    # 开始录制
    if(input("输入yes开始录制") == "y"):
        adb = AdbService()
        adb.start()
    if(input("输入yes停止录制") == "y"):
        _Recording = False
    __play = True
    while __play:
        if(input("输入yes开始回放") == "y"):
            ue = UserPlay()
            ue.play()
        else:
            __play = False
        
    # 停止录制
    # 设置循环
else:
    print("没有找到ANDROID_HOME")
    exit()
    
