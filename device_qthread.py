# -*- coding: UTF-8 -*-
# @Time    : 2025/1/6 13:48
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : device_qthread.py
# @IDE     : PyCharm
import time

from PyQt5.QtCore import QThread, pyqtSignal

from config_data import Config_Data
from device_csv_util import Device_Csv_Util
from device_info_util import Dev_Info_Util
from upgrade_manager import Upgrade_Manager
from upgrade_status import Upgrade_Status


class Device_QThread(QThread):
    # 信号类型:int(升级单元对象id), str(事件名), list(数据列表)
    call_fun_signal = pyqtSignal(int, str, list)
    mQuerying = False

    def run(self):
        try:
            Device_QThread.mQuerying = True

            # 使用Q线程、查询设备信息(防止UI线程阻塞)
            for tmpCell in Upgrade_Manager.mCells:
                last_tick = time.time()

                boQuerySuccess = False
                # 获取设备信息
                while True:
                    tmpSecs = int(time.time() - last_tick)
                    print(f"[{tmpCell.mIndex}] query device information wait time:{tmpSecs}(s)")
                    # 获取设备信息(每隔几秒获取一次)
                    if tmpSecs % 2 == 0:
                        boState, lstValue, strMsg = Dev_Info_Util.getDevInfo(tmpCell.mComNum)
                        if not boState:
                            # 超时 (将升级状态设置为失败)
                            if tmpSecs >= Config_Data.DEV_INFO_MAX_WAIT_TIME:
                                print(f"[{tmpCell.mIndex}] Failed to query device information by over time:{tmpSecs}(s)")
                                break
                        else:
                            # 保存设备信息
                            tmpCell.mVersion = lstValue[0]
                            tmpCell.mMacAddress = lstValue[1]
                            boQuerySuccess = True
                            break
                    time.sleep(1)

                if boQuerySuccess:
                    tmpRecord = Device_Csv_Util.find_record_by_mac(Device_Csv_Util.getFileName(), tmpCell.mMacAddress)
                    if tmpRecord is not None:
                        tmpRecord["Mac"] = tmpCell.mMacAddress
                        tmpRecord["Version"] = tmpCell.mVersion
                    else:
                        tmpRecord = {}
                        noneValue = Upgrade_Status.RLT_STATE_NONE
                        noneStateValue = f"0#{noneValue}"
                        tmpRecord["Mac"] = tmpCell.mMacAddress
                        tmpRecord["Version"] = tmpCell.mVersion
                        tmpRecord["BT"] = noneStateValue
                        tmpRecord["Voice"] = noneStateValue
                        tmpRecord["Demo"] = noneStateValue
                        tmpRecord["OpTime"] = noneValue

                    self.call_fun_signal.emit(tmpCell.mIndex, Upgrade_Status.SI_TAG_QUERY_INFO, [True, tmpRecord])
                else:
                    tmpCell.mVersion = Upgrade_Status.RLT_STATE_NONE
                    tmpCell.mMacAddress = Upgrade_Status.RLT_STATE_NONE

                    tmpRecord = {}
                    noneValue = Upgrade_Status.RLT_STATE_NONE
                    noneStateValue = f"0#{noneValue}"
                    tmpRecord["Mac"] = noneValue
                    tmpRecord["Version"] = f"{noneValue}#{noneValue}#{noneValue}"
                    tmpRecord["BT"] = noneStateValue
                    tmpRecord["Voice"] = noneStateValue
                    tmpRecord["Demo"] = noneStateValue
                    tmpRecord["OpTime"] = noneValue

                    self.call_fun_signal.emit(tmpCell.mIndex, Upgrade_Status.SI_TAG_QUERY_INFO, [False, tmpRecord])

            time.sleep(1)
        except Exception as e:
            print("Device_QThread: query device information error?" + repr(e))
        finally:
            Device_QThread.mQuerying = False
            # 这里传第一个对象的索引值(主要与数据类型相匹配,无其它意义)
            self.call_fun_signal.emit(Upgrade_Manager.mCells[0].mIndex, Upgrade_Status.SI_TAG_QUERY_END, [])