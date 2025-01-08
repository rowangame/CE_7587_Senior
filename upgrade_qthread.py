# -*- coding: UTF-8 -*-
# @Time    : 2024/12/26 13:51
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : upgrade_qthread.py
# @IDE     : PyCharm
import os
import time

from PyQt5.QtCore import QThread, pyqtSignal

from cmodule_proxy import CModule_Proxy
from config_data import Config_Data
from device_info_util import Dev_Info_Util
from local_data_util import Local_Data_Util
from upgrade_cell import Upgrade_Cell
from upgrade_status import Upgrade_Status


class Upgrade_QThread(QThread):
    # 信号类型:int(升级单元对象id), str(事件名), list(数据列表)
    call_fun_signal = pyqtSignal(int, str, list)

    def __init__(self, upCell: Upgrade_Cell, parent=None):
        super(Upgrade_QThread, self).__init__(parent)
        self.mUpgradeCell = upCell

    def run(self):
        try:
            # 初始化开始环境
            self.mUpgradeCell.initUpgradeStartEnv()

            # C模块升级对象
            cmodule_proxy_obj = CModule_Proxy(self, self.mUpgradeCell)
            self.mUpgradeCell.mCModuleProxy = cmodule_proxy_obj

            # 设置状态为升级逻辑处理中
            self.mUpgradeCell.mUpgradeProcessing = True
            # 记录开始时间
            self.mUpgradeCell.mProcessStartTime = time.strftime("%H:%M:%S", time.localtime())
        except Exception as e:
            print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: initialize env error?" + repr(e))

        # 升级逻辑处理
        try:
            self.doUpgradeProcess()
        except Exception as e:
            print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: doUpgradeProcess error?" + repr(e))
        finally:
            # 警告: Q线程运行结速后,必须设置升级逻辑状态为False,否则ui界面,会显示升级状态中。不能正常退出主界面
            self.mUpgradeCell.mUpgradeProcessing = False
            # 记录结束时间
            self.mUpgradeCell.mProcessEndTime = time.strftime("%H:%M:%S", time.localtime())
            # 发送升级逻辑处理结束消息
            self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_PROCESS_END, [])

    def doUpgradeProcess(self):
        # 对升级类型顺序升级
        upTypeCnt = len(self.mUpgradeCell.mUpgradeTypeLst)
        for tmpTypeIndex in range(upTypeCnt):
            # 设置升级状态,用于等待当前类型升级结束后,继续下一个升级类型
            self.mUpgradeCell.mUpgrading = True
            # 设置升级状态:数据同步中
            self.mUpgradeCell.mUpgradeState = Upgrade_Status.BS_REQUEST_SYNC
            # 临时状态(用于是否要继续升级)
            tmpNeedUpgrade = True
            # 设置类型索引值
            self.mUpgradeCell.mUpgradeIndex = tmpTypeIndex
            # 发送单个类型升级开始(通知状态刷新)
            self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_UPGRADE_START, [])
            # 这里等待几秒钟(减少UI显示获得锁资源冲突的概率)
            tmpSleepTime = 2
            if tmpTypeIndex == 0:
                tmpSleepTime += (self.mUpgradeCell.mIndex - 1) * 2
            else:
                tmpSleepTime += self.mUpgradeCell.mIndex
            time.sleep(tmpSleepTime)

            try:
                last_tick = time.time()
                # 获取设备信息
                while True:
                    time.sleep(1)
                    tmpSecs = int(time.time() - last_tick)
                    self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_DEV_INFO_SECS, [tmpSecs])
                    # 获取设备信息(每隔几秒获取一次)
                    if tmpSecs % 2 == 0:
                        boState, lstValue, strMsg = Dev_Info_Util.getDevInfo(self.mUpgradeCell.mComNum)
                        if not boState:
                            # 超时 (将升级状态设置为失败)
                            if tmpSecs >= Config_Data.DEV_INFO_MAX_WAIT_TIME:
                                tmpNeedUpgrade = False

                                # 设置升级结果状态为失败
                                self.mUpgradeCell.mUpgradeResult[tmpTypeIndex] = Upgrade_Status.RLT_STATE_FAIL
                                self.mUpgradeCell.mUpgradeState = Upgrade_Status.BS_UPGRADE_ERROR
                                self.mUpgradeCell.mUpgrading = False
                                self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_END, [])
                                break
                        else:
                            # 保存设备信息
                            self.mUpgradeCell.mVersion = lstValue[0]
                            self.mUpgradeCell.mMacAddress = lstValue[1]
                            break

                # 如果需要更新(查询设备成功,通知UI显示)
                if tmpNeedUpgrade:
                    self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_DEV_INFO_RLT,
                                              [self.mUpgradeCell.mVersion, self.mUpgradeCell.mMacAddress])
                    time.sleep(2)
            except Exception as e:
                print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: get device info error?" + repr(e))

            if not tmpNeedUpgrade:
                # 等待UI显示刷新
                time.sleep(2)
                continue
            try:
                # 比较版本类型[选择强制升级后,不会比较版本号]
                if not Local_Data_Util.fwSharedData["stressUpgrade"]:
                    tmpVersion = self.mUpgradeCell.mVersion
                    tmpFwFilePath = self.mUpgradeCell.mUpgradeBinLst[tmpTypeIndex]
                    tmpUpType = self.mUpgradeCell.mUpgradeTypeLst[tmpTypeIndex]

                    if len(tmpFwFilePath) == 0:
                        tmpNeedUpgrade = False
                    else:
                        if not self.compareVersion(tmpVersion, tmpFwFilePath, tmpUpType):
                            tmpNeedUpgrade = False

                    if tmpNeedUpgrade:
                        self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_CMP_VERSION, ["Yes"])
                    else:
                        self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_CMP_VERSION, ["No"])
                    # 等待UI显示刷新
                    time.sleep(2)

                    if not tmpNeedUpgrade:
                        # 设置升级结果状态为忽略
                        self.mUpgradeCell.mUpgradeResult[tmpTypeIndex] = Upgrade_Status.RLT_STATE_IGNORE
                        self.mUpgradeCell.mUpgradeState = Upgrade_Status.BS_UPGRADE_IGNORE
                        self.mUpgradeCell.mUpgrading = False
                        self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_END, [])
            except Exception as e:
                print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: compare device version error?" + repr(e))

            if not tmpNeedUpgrade:
                # 等待UI显示刷新
                time.sleep(2)
                continue
            try:
                boCommonEnd = True
                last_tick = time.time()
                # 启动C模块升级
                self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_COPEN, [])
                # 等待C模块进程结束,超时需要强制结束当前逻辑
                while True:
                    time.sleep(1)
                    if not self.mUpgradeCell.mUpgrading:
                        # 这里等待几秒钟,让UI线程显示当前类型的结束状态
                        time.sleep(2)
                        break
                    spared_secs = int(time.time() - last_tick)
                    if spared_secs >= Config_Data.UPGRADE_MAX_WAIT_TIME:
                        boCommonEnd = False
                        print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: c module process over time! secs:{spared_secs}")
                        break
                if not boCommonEnd:
                    # 如果当前C进程没结束(可能需要强制结束进程)
                    if self.mUpgradeCell.mCModuleStateThread is not None:
                        sTag = f"[{self.mUpgradeCell.mIndex}] "
                        sInfo = "Upgrade_QThread: c module process error? mCModuleStateThread is not None!"
                        print(f"{sTag}{sInfo}")
                    if self.mUpgradeCell.mCModuleThread is not None:
                        sTag = f"[{self.mUpgradeCell.mIndex}] "
                        sInfo = "Upgrade_QThread: c module process error? mCModuleThread is not None!"
                        print(f"{sTag}{sInfo}")

                    # 设置状态并通知ui显示
                    self.mUpgradeCell.mUpgradeResult[tmpTypeIndex] = Upgrade_Status.RLT_STATE_FAIL
                    self.mUpgradeCell.mUpgradeState = Upgrade_Status.BS_UPGRADE_ERROR
                    self.mUpgradeCell.mUpgrading = False
                    self.call_fun_signal.emit(self.mUpgradeCell.mIndex, Upgrade_Status.SI_TAG_END, [])

                    # 等待ui刷新显示
                    time.sleep(2)
            except Exception as e:
                print(f"[{self.mUpgradeCell.mIndex}] Upgrade_QThread: c module process error?" + repr(e))

    def compareVersion(self, verSrc: str, fwFilePath: str, upType: str):
        """
        :param verSrc:
            版本信息: xx#xx#xx#xx
        :param fwFilePath:
            bin文件路径
        :param upType:
            升级类型: bt,demo,voice
        :return:
            True: 需要升级 False: 忽略版本
        """
        try:
            lstVer = verSrc.split("#")
            fileName = os.path.basename(fwFilePath)
            if upType == Local_Data_Util.FW_TYPE_BT:
                # XG_BT_FW_241209_1380A_PV1_4OHM_DFU.bin
                cells = fileName.split("_")
                fileVersion = cells[3] + "." + cells[4]
                devVersion = lstVer[0]

                return devVersion != fileVersion
            elif upType == Local_Data_Util.FW_TYPE_VOICE:
                # combined_prompt_V07_DFU.bin
                cells = fileName.split("_")
                # 去掉文件名带'V'的字符
                fileVersion = cells[2][1:]
                devVersion = lstVer[1]

                return devVersion != fileVersion
            else:
                # demoplay_sample_V02.bin
                cells = fileName.split("_")
                # 去掉文件名带'V'的字符
                fileVersion = cells[2][1:3]
                devVersion = lstVer[2]

                return devVersion != fileVersion
        except Exception as e:
            print(f"[{self.mUpgradeCell.mIndex}] Compare version occurs error:" + repr(e))
        return True
