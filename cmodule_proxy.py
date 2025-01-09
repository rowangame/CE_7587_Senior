# -*- coding: UTF-8 -*-
# @Time    : 2024/12/26 17:56
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : cmodule_proxy.py
# @IDE     : PyCharm
import mmap
import os
import subprocess
import threading
import time

from language_util import Language_Util
from local_data_util import Local_Data_Util
from upgrade_logger import Upgrade_Logger
from upgrade_status import Upgrade_Status


class CModule_Proxy:
    C_TAG_START = "#<"
    C_TAG_END = ">"

    C_MSG_INFO = 1
    C_MSG_ERROR = 2
    C_MSG_EXCEPT = 3
    C_MSG_PROGRESS = 4
    C_MSG_BURN_STATE = 5

    C_BURN_STATE_INIT = 0
    C_BURN_STATE_START = 1
    C_BURN_STATE_REQ_BURN = 2
    C_BURN_STATE_DATA_TRANSFER = 3
    C_BURN_STATE_DATA_FINISH = 4
    C_BURN_STATE_REQ_END = 5
    C_BURN_STATE_END_SUCCESS = 6
    C_BURN_STATE_END_FAIL = 7

    def __init__(self, qThreadObj, upgradeCell):
        """
        :param qThreadObj:
            q线程对象,UI数据刷新用到
        :param upgradeCell:
            升级单元对象,整个回调后,需要确定对象是哪个升级单元对象的升级
        """
        self.mQthreadObj = qThreadObj
        self.mUgradeCell = upgradeCell

    def canSendMsg(self):
        return (self.mQthreadObj is not None) and (self.mQthreadObj.call_fun_signal is not None)

    def showInfo(self, info: str, errorTag: str):
        Upgrade_Logger.addConsoleLog(self.mUgradeCell.mIndex, info)

        # 警告,这里的信号对象只能是信号对象所有者调用。否则会出现emit属于不存在的问题
        if self.canSendMsg():
            self.mQthreadObj.call_fun_signal.emit(self.mUgradeCell.mIndex, errorTag, [info])

    def start_cmodule_proxy(self):
        process = None

        execPath = self.mUgradeCell.mModulePath
        try:
            upIndex = self.mUgradeCell.mUpgradeIndex

            comType = self.mUgradeCell.mComNum
            binTypeValue = str(Local_Data_Util.getUpgradeTypeValueEx(self.mUgradeCell.mUpgradeTypeLst[upIndex]))
            fwPath = self.mUgradeCell.mUpgradeBinLst[upIndex]
            mmShareName = self.mUgradeCell.generateShareMMName()

            """
            警告：在使用QThread线程内使用subprocess.Popen函数,调用c模块会失败。可能是
            线程上下文差异:
                在 PyQt5 中，QThread 的运行环境与主线程有所不同。subprocess.Popen 可能依赖于一些仅在主线程中可用的资源或环境变量，
                例如 GUI 线程中的某些资源，可能会导致子进程在 QThread 中无法正确启动
            信号与槽机制:
                QThread 和主线程的交互可能存在竞态条件，尤其是涉及信号与槽的异步操作时。
                某些资源或对象可能在 QThread 中不可用，或者在你启动子进程之前还未初始化完成。
            线程安全问题:
                subprocess.Popen 本身是线程安全的，但如果你的 C++ 模块或其他依赖项不是线程安全的，在不同线程中调用它们可能会导致异常行为。
            资源锁定:
                如果你的 C++ 模块需要访问某些系统资源，如文件、设备或网络端口，这些资源可能会被主线程锁定，从而在子线程中无法访问
            环境变量和工作目录:
                当你在子线程中调用 subprocess.Popen 时，默认的工作目录和环境变量可能会有所不同。
                你可以在 subprocess.Popen 调用中显式指定 cwd（当前工作目录）和 env（环境变量）来确保一致性
            GIL（全局解释器锁）:
                Python 的全局解释器锁（GIL）可能在多线程环境中影响某些操作。
                虽然 GIL 不直接影响 C++ 模块的执行，但可能影响到 Python 与 C++ 之间的某些交互
            """
            # 使用subprocess.Popen来启动程序并捕获输出
            process = subprocess.Popen(
                [execPath] + [comType, fwPath, str(binTypeValue), mmShareName],
                stdout=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏控制台窗口
            )

            # communicate() 用于与子进程交互，并获取完整的输出
            # 注意:stdout和stderr是字节字符串,可能需要解码成文本格式
            # stdout, stderr = process.communicate()

            # 等待进程结束并获取退出状态
            process.wait()

            # 等待结束
            self.mUgradeCell.mCModuleWaiting = False
        except FileNotFoundError:
            self.showInfo(f"C{Language_Util.getValue('cm_not_found')}:{execPath}", Upgrade_Status.SI_TAG_ERROR)
        except Exception as e:
            self.showInfo(f"{Language_Util.getValue('cm_exe_error')}:{repr(e)}", Upgrade_Status.SI_TAG_ERROR)
        finally:
            # 等待结束
            self.mUgradeCell.mCModuleWaiting = False

            # 等待数据读取线程结束,防止状态混乱
            if self.mUgradeCell.mCModuleStateThread is not None:
                self.mUgradeCell.mCModuleStateThread.join()
                self.mUgradeCell.mCModuleStateThread = None

            if process is not None:
                # 确保进程已结束并清理资源 (如果进程还在运行)
                if process.poll() is None:
                    # 终止进程
                    process.terminate()
                if process.stdout is not None:
                    process.stdout.close()
            # 通知ui结束事件
            self.showInfo("end", Upgrade_Status.SI_TAG_END)

    def showCModuleWaiting(self):
        seconds = 0
        lastTickMs = 0
        while True:
            curTickMs = int(time.time() * 1000)
            if curTickMs - lastTickMs > 1000:
                lastTickMs = curTickMs
                seconds += 1
                if self.canSendMsg():
                    self.mQthreadObj.call_fun_signal.emit(self.mUgradeCell.mIndex, Upgrade_Status.SI_TAG_CMODULE_WAIT, [seconds])
            if not self.mUgradeCell.mCModuleWaiting:
                break
            time.sleep(0.2)

    def showCModuleState(self):
        # 警告:
        # 用Python subprocess.open方法调用C++进程时,如果这个进行在创建共享内存对象时,
        # Python程序先创造一个内存访问对象,则C++进程无法创建共享对象,会出现错误代码(id:87)
        # Chat GPT4.0 给出的可能原因是权限不够，其实是访问冲突导致的，AI有局限性。必须认真分析问题
        # 否则，问题卡个几个月也是有可能
        # 因此这里等待了几秒钟的时间,让C++进程能成功创建共享内存
        SAFE_WAIT_TIME_SECS = 8
        seconds = 0
        lastTickMs = 0
        while True:
            curTickMs = int(time.time() * 1000)
            if curTickMs - lastTickMs > 1000:
                lastTickMs = curTickMs
                seconds += 1
                if self.canSendMsg():
                    self.mQthreadObj.call_fun_signal.emit(self.mUgradeCell.mIndex, Upgrade_Status.SI_TAG_CMODULE_WAIT, [seconds])
            time.sleep(0.2)
            if seconds >= SAFE_WAIT_TIME_SECS:
                break
            # 与C模块共享内存一至大小
        SHARED_MEMORY_SIZE = 512 * 1024

        shared_memory = None
        try:
            readIndex = 0

            msgInfoSize = 4
            startIndex = msgInfoSize
            perSize = 128  # sizeof(unsigned short) + sizeof(unsigned char) + sizeof(char buffer[125])

            lastTick = time.time()
            max_retry_time = 20

            # 打开共享内存
            shared_memory = mmap.mmap(-1, SHARED_MEMORY_SIZE, tagname=self.mUgradeCell.mMMShareName, access=mmap.ACCESS_READ)
            while True:
                shared_memory.seek(0)

                btMsgInfo = shared_memory.read(msgInfoSize)
                curIndex = int.from_bytes(btMsgInfo[0:2], byteorder="little", signed=False)
                isEnd = int.from_bytes(btMsgInfo[2:3], byteorder="little", signed=False)
                reserved = int.from_bytes(btMsgInfo[3:4], byteorder="little", signed=False)

                if readIndex < curIndex:
                    # 移动到指定的起始位置
                    shared_memory.seek(startIndex)
                    # 从该位置读取指定长度的数据
                    data = shared_memory.read(perSize)
                    """
                    struct MyMsgData {
                            unsigned short index;       // 当前数据索引位
                            unsigned char len;          // 消息长度
                            char buffer[125];           // 消息内容
                    };
                    """
                    # 这里与c++模块内存共享数据内容一致
                    # idxMsgData = data[0:2]
                    # tmpReadIndex = int.from_bytes(idxMsgData, byteorder="little", signed=False)
                    tmpMsgLen = int(data[2:3][0])
                    line = ""
                    if tmpMsgLen > 0:
                        line = data[3:3 + tmpMsgLen].decode("GBK")
                    # print(f"tmpReadIndex={tmpReadIndex}, msgLen={tmpMsgLen} ctx={line}")
                    if len(line) > 0:
                        try:
                            # 分析进行打印的提示值
                            if line.startswith(CModule_Proxy.C_TAG_START):
                                sIdx = len(CModule_Proxy.C_TAG_START)
                                eIdx = line.find(CModule_Proxy.C_TAG_END)
                                # 状态值
                                tmpState = int(line[sIdx:eIdx])
                                # 提示值
                                tmpValue = line[eIdx + 1:len(line)]
                                # print(f"tmpState={tmpState} tmpValue={tmpValue}")
                                # 分析状态值
                                if tmpState == CModule_Proxy.C_MSG_BURN_STATE:
                                    # 得到状态数值(#<5>state=x)
                                    burnState = tmpValue.split("=")[1]
                                    self.analyzeUpgradeState(int(burnState))
                                elif tmpState == CModule_Proxy.C_MSG_PROGRESS:
                                    # 得到进度数据 (#<4>Upgrading:<x%>\n)
                                    strProgressValue = tmpValue.split(":")[1]
                                    # 去掉左边的 "<" 和右边的 "%>" 得到数值
                                    strProgress = strProgressValue[1:len(strProgressValue) - 3]
                                    tmpProgress = int(strProgress)
                                    self.handleProgress(tmpProgress)
                                else:
                                    # 这里需要去掉\n字符(解决控制台打印多出的空行问题)
                                    if tmpValue.endswith("\n"):
                                        tmpValue = tmpValue[0:len(tmpValue)-1]
                                    self.handleMessage(tmpState, tmpValue)
                        except Exception as e:
                            print(f"[{self.mUgradeCell.mIndex}] showCModuleState.read error?" + repr(e))

                    startIndex += perSize
                    readIndex += 1
                    lastTick = time.time()

                # 当共享数据缓冲区有数据时,直接读取(不需要判断结束标记,解决读取数据不完全的问题)
                if readIndex < curIndex:
                    time.sleep(0.2)
                    continue

                # 结束标记
                if isEnd > 0:
                    Upgrade_Logger.addConsoleLog(self.mUgradeCell.mIndex, f"End status:{isEnd} totalIndex={curIndex}")
                    break

                curTick = time.time()
                dtime = curTick - lastTick
                if dtime > max_retry_time:
                    Upgrade_Logger.addConsoleLog(self.mUgradeCell.mIndex, f"Data read timeout:dtime={dtime}>{max_retry_time}(s)")
                    break
                if not self.mUgradeCell.mCModuleWaiting:
                    break
                time.sleep(0.2)
        except Exception as e:
            print(f"[{self.mUgradeCell.mIndex}] showCModuleState.process error?" + repr(e))
        finally:
            if shared_memory is not None:
                # 确保共享内存对象被正确关闭
                shared_memory.close()

    def analyzeUpgradeState(self, bsState: int):
        lastUpState = self.mUgradeCell.mUpgradeState

        if bsState == CModule_Proxy.C_BURN_STATE_INIT:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_REQUEST_SYNC
        elif bsState == CModule_Proxy.C_BURN_STATE_START:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_REQUEST_SYNC
        elif bsState == CModule_Proxy.C_BURN_STATE_REQ_BURN:
            self.mUgradeCell.mUpgradeState= Upgrade_Status.BS_REQUEST_SYNC
        elif bsState == CModule_Proxy.C_BURN_STATE_DATA_TRANSFER:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_DATA_TRANSFER
        elif bsState == CModule_Proxy.C_BURN_STATE_DATA_FINISH:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_DATA_TRANSFER_END
        elif bsState == CModule_Proxy.C_BURN_STATE_REQ_END:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_DATA_TRANSFER_END
        elif bsState == CModule_Proxy.C_BURN_STATE_END_SUCCESS:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_UPGRADE_SUCCESS
        elif bsState == CModule_Proxy.C_BURN_STATE_END_FAIL:
            self.mUgradeCell.mUpgradeState = Upgrade_Status.BS_UPGRADE_ERROR

        # 通知状态显示(状态发生改变才会通知)
        if (self.mUgradeCell.mUpgradeState != lastUpState) and self.canSendMsg():
            self.mQthreadObj.call_fun_signal.emit(self.mUgradeCell.mIndex, Upgrade_Status.SI_TAG_CHSTATE, [bsState])

    def handleProgress(self, progress: int):
        boNotify = self.mUgradeCell.mUpgradeProgress != progress
        self.mUgradeCell.mUpgradeProgress = progress
        # 只有进度有更新时,才通知进度更新显示
        if boNotify and self.canSendMsg():
            self.mQthreadObj.call_fun_signal.emit(self.mUgradeCell.mIndex,
                                                  Upgrade_Status.SI_TAG_PROGRESS, [f"Progress:{progress}%"])

    def handleMessage(self, state: int, msg: str):
        if state == CModule_Proxy.C_MSG_INFO:
            self.showInfo(msg, Upgrade_Status.SI_TAG_INFO)
        elif state == CModule_Proxy.C_MSG_ERROR:
            self.showInfo(msg, Upgrade_Status.SI_TAG_ERROR)
        elif state == CModule_Proxy.C_MSG_EXCEPT:
            self.showInfo(msg, Upgrade_Status.SI_TAG_EXCEPT)

    def startUpgrade(self):
        self.showInfo(f"C Module directory: {self.mUgradeCell.mModulePath}", Upgrade_Status.SI_TAG_INFO)

        cModuleThread = threading.Thread(target=self.start_cmodule_proxy, args=())
        cModuleThread.start()
        self.mUgradeCell.mCModuleThread = cModuleThread

        self.mUgradeCell.mCModuleWaiting = True
        cModuleStateThread = threading.Thread(target=self.showCModuleState)
        cModuleStateThread.start()
        self.mUgradeCell.mCModuleStateThread = cModuleStateThread