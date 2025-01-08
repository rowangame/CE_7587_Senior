# -*- coding: UTF-8 -*-
# @Time    : 2024/9/26 16:59
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : local_data_util.py
# @IDE     : PyCharm
import os
import pickle


class Local_Data_Util:
    # bt 文件类型 (固件文件选择升级类型相关)
    FW_TYPE_BT = "bt"

    # voice 文件类型 (固件文件选择升级类型相关)
    FW_TYPE_VOICE = "voice"

    # demo 文件类型 (固件文件选择升级类型相关)
    FW_TYPE_DEMO = "demo"

    # 升级类型(c模块协议)
    MODULE_TYPE_C = "c"

    # 升级类型(python模块协议)
    MODULE_TYPE_PY = "py"

    # bt类型对应的数值
    FW_VALUE_BT = 0x00

    # voice类型对应的数值
    FW_VALUE_VOICE = 0x02

    # demo类型对应的数值
    FW_VALUE_DEMO = 0x03

    # 当前选择的文件数据(本地与内存共享)
    fwSharedData = {
        "btPath": "",           # bt 类型文件路径
        "voicePath": "",        # voice 类型文件路径
        "demoPath": "",         # demo 类型文件路径
        "sltType": "bt",        # 选中的类型("bt","voice","demo","auto"类型 默认选择bt类型)
        "moduleType": "c",      # 升级类型(”c":c模块协议,"py":python模块协议[弃用])
        "language": "CN",       # 当前选择的语言(默认为:中文)
        "autoUpgrade": False,   # 是否选中了(自动升级方式: BT,VOICE,DEMO类型按顺序升级)
        "stressUpgrade": True   # 强制升级(选择强制升级后,不会比较版本号)
    }

    mLoaded: bool = False       # 是否从本地加载了数据

    @classmethod
    def loadData(cls):
        """
        加载本地数据
        :return state:
            True(加载成功)
            False(加载失败)
        data:
            "fw_path" 固件文件目录
        """
        filePath = os.getcwd() + "\\data\\data.pickle"
        if os.path.exists(filePath):
            try:
                tmpFile = open(filePath, 'rb')
                cls.fwSharedData = pickle.load(tmpFile)
                cls.mLoaded = True

                return True
            except Exception as e:
                print("loadData error?" + repr(e))

        return False

    @classmethod
    def saveData(cls):
        """
        保存数据对象到本地
        :param data:
            数据对象,带bin文件路径的数据
        :return:
            state: True(成功) False(失败)
        """
        try:
            filePath = os.getcwd() + "\\data\\data.pickle"
            tmpFile = open(filePath, 'wb')
            pickle.dump(Local_Data_Util.fwSharedData, tmpFile)
            tmpFile.close()
            return True
        except Exception as e:
            print(repr(e))
        return False

    @classmethod
    def getUpgradeTypeValue(cls):
        """
        得到升级文件的类型参数
        :return:
            00:bt voice:02 demo:03
        """
        kValues = {
            "bt": cls.FW_VALUE_BT,
            "voice": cls.FW_VALUE_VOICE,
            "demo": cls.FW_VALUE_DEMO
        }
        return kValues[cls.fwSharedData["sltType"]]

    @classmethod
    def getUpgradeTypeValueEx(cls, upType: str):
        """
        得到升级文件的类型参数
        :parameter upType:
            升级类型
        :return:
            00:bt voice:02 demo:03
        """
        kValues = {
            "bt": cls.FW_VALUE_BT,
            "voice": cls.FW_VALUE_VOICE,
            "demo": cls.FW_VALUE_DEMO
        }
        return kValues[upType]

    @classmethod
    def getUpgradeBinFile(cls):
        """
        根据默认的升级类型,得到bin文件本地路径
        :return:
           bin文件路径
        """
        if cls.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_BT:
            return cls.fwSharedData["btPath"]
        elif cls.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_VOICE:
            return cls.fwSharedData["voicePath"]
        else:
            return cls.fwSharedData["demoPath"]

    @classmethod
    def getUpgradeBinFileEx(cls, upType: str):
        """
        根据默认的升级类型,得到bin文件本地路径
        :return:
           bin文件路径
        """
        if upType == Local_Data_Util.FW_TYPE_BT:
            return cls.fwSharedData["btPath"]
        elif upType == Local_Data_Util.FW_TYPE_VOICE:
            return cls.fwSharedData["voicePath"]
        else:
            return cls.fwSharedData["demoPath"]

    @classmethod
    def checkBinPath(cls):
        if cls.fwSharedData["autoUpgrade"]:
            return len(cls.fwSharedData["btPath"]) > 0
        else:
            if cls.fwSharedData["sltType"] == cls.FW_TYPE_BT:
                return len(cls.fwSharedData["btPath"]) > 0
            elif cls.fwSharedData["sltType"] == cls.FW_TYPE_VOICE:
                return len(cls.fwSharedData["voicePath"]) > 0
            else:
                return len(cls.fwSharedData["demoPath"]) > 0

