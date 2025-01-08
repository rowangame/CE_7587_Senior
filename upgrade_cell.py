# -*- coding: UTF-8 -*-
# @Time    : 2024/12/25 15:26
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : upgrade_cell.py
# @IDE     : PyCharm
import os
import random

from local_data_util import Local_Data_Util
from upgrade_status import Upgrade_Status


class Upgrade_Cell:
    def __init__(self, index, com):
        # 序号ID (显示状态和启动C模块程序有关)
        self.mIndex = index

        # 串口类型
        self.mComNum = com

        # 当前状态
        self.mUpgradeState = Upgrade_Status.BS_FREE

        # 观查者对象
        self.mObserver = None
        # 是否是升级状态(单个升级类型状态)
        self.mUpgrading = False
        # 是否是升级逻辑中状态(包含自动升级方式,用于判断ui进程是否能安全退出)
        self.mUpgradeProcessing = False
        # 升级线程
        self.mUpgradeThread = None

        # C模块相关状态数据
        self.mModulePath = ""
        self.mCModuleThread = None
        self.mCModuleStateThread = None
        self.mCModuleWaiting = False
        self.mCModuleProxy = None

        # 开始时间(单个类型)
        self.mStartTime = ""
        # 结束时间(单个类型)
        self.mEndTime = ""
        # 开始时间(整个逻辑)
        self.mProcessStartTime = ""
        # 结束时间(整个逻辑)
        self.mProcessEndTime = ""

        # 当前升级的索引值(单个升级为:0,自动升级为:0,1,2)
        self.mUpgradeIndex = 0
        # 要升级类型列表
        self.mUpgradeTypeLst = []
        # 要升级文件列表
        self.mUpgradeBinLst = []
        # 升级结果记录
        self.mUpgradeResult = []

        # 设备信息(版本号)
        self.mVersion = ""
        # mac地址信息
        self.mMacAddress = ""
        # 当前进度
        self.mUpgradeProgress = 0

    def clear(self):
        self.mIndex = 0
        self.mComNum = ""
        self.mUpgradeState = Upgrade_Status.BS_FREE

        self.mObserver = None
        self.mUpgrading = False
        self.mUpgradeProcessing = False
        self.mUpgradeThread = None

        self.mModulePath = ""
        self.mCModuleThread = None
        self.mCModuleStateThread = None
        self.mCModuleWaiting = False
        self.mCModuleProxy = None

        self.mStartTime = ""
        self.mEndTime = ""
        self.mProcessStartTime = ""
        self.mProcessEndTime = ""
        self.mUpgradeIndex = 0
        self.mUpgradeTypeLst.clear()
        self.mUpgradeBinLst.clear()
        self.mUpgradeResult.clear()

        self.mVersion = ""
        self.mMacAddress = ""
        self.mUpgradeProgress = 0

    def generateShareMMName(self):
        """
        生成共享内存数据块名字(为同时多个串口升级做适配)
        :return:
        """
        self.mMMShareName = "SHARE_%s_%02d" % (self.mComNum, random.randint(1, 100))
        return self.mMMShareName

    def initUpgradeStartEnv(self):
        self.mVersion = ""
        self.mMacAddress = ""
        # 设置升级类型列表
        self.mUpgradeTypeLst.clear()
        self.mUpgradeBinLst.clear()
        self.mUpgradeResult.clear()

        if not Local_Data_Util.fwSharedData["autoUpgrade"]:
            self.mUpgradeIndex = 0
            self.mUpgradeTypeLst.append(Local_Data_Util.fwSharedData["sltType"])
            self.mUpgradeBinLst.append(Local_Data_Util.getUpgradeBinFileEx(self.mUpgradeTypeLst[0]))
            self.mUpgradeResult.append(Upgrade_Status.RLT_STATE_NONE)
        else:
            # 自动升级方式按(BT,DEMO,VOICE方式升级)
            self.mUpgradeIndex = 0
            self.mUpgradeTypeLst.append(Local_Data_Util.FW_TYPE_BT)
            self.mUpgradeTypeLst.append(Local_Data_Util.FW_TYPE_DEMO)
            self.mUpgradeTypeLst.append(Local_Data_Util.FW_TYPE_VOICE)
            for i in range(len(self.mUpgradeTypeLst)):
                self.mUpgradeBinLst.append(Local_Data_Util.getUpgradeBinFileEx(self.mUpgradeTypeLst[i]))
                self.mUpgradeResult.append(Upgrade_Status.RLT_STATE_NONE)

        # C模块路径
        self.mModulePath = os.getcwd() + "\\cmodule\\CM%02d\\Burn_Tool.exe" % self.mIndex

    def refreshVersionByFilename(self):
        try:
            upType = self.mUpgradeTypeLst[self.mUpgradeIndex]
            fwFilePath = self.mUpgradeBinLst[self.mUpgradeIndex]
            fileVersion = self.getVersionByFilename(upType, fwFilePath)

            # csv文件保存的版本类型格式是 bt#voice#demo
            verLst = self.mVersion.split("#")
            if upType == Local_Data_Util.FW_TYPE_BT:
                verLst[0] = fileVersion
            elif upType == Local_Data_Util.FW_TYPE_VOICE:
                verLst[1] = fileVersion
            else:
                verLst[2] = fileVersion

            # 更新版本号
            self.mVersion = f"{verLst[0]}#{verLst[1]}#{verLst[2]}"
        except Exception as e:
            print(f"[{self.mIndex}] refreshVersionByFilename error?" + repr(e))

    @classmethod
    def getVersionByFilename(cls, upType: str, fwFilePath: str):
        fileName = os.path.basename(fwFilePath)
        if upType == Local_Data_Util.FW_TYPE_BT:
            # 例如:XG_BT_FW_241209_1380A_PV1_4OHM_DFU.bin
            cells = fileName.split("_")
            fileVersion = cells[3] + "." + cells[4]
            return fileVersion
        elif upType == Local_Data_Util.FW_TYPE_VOICE:
            # 例如:combined_prompt_V07_DFU.bin
            cells = fileName.split("_")
            # 去掉文件名带'V'的字符
            fileVersion = cells[2][1:]
            return fileVersion
        else:
            # 例如:demoplay_sample_V02.bin
            cells = fileName.split("_")
            fileVersion = cells[2][1:3]
            return fileVersion
