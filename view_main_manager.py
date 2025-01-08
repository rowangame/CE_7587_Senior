# -*- coding: UTF-8 -*-
# @Time    : 2024/12/25 16:30
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : view_main_manager.py
# @IDE     : PyCharm
import os
import threading
import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPalette, QFont, QStandardItemModel, QStandardItem, QBrush, QColor, QIcon
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QMainWindow, QAction, QActionGroup, QLabel

from center_delegate import CenterDelegate
from config_data import Config_Data
from device_csv_util import Device_Csv_Util
from device_filepath_util import Device_Filepath_Util
from device_qthread import Device_QThread
from language_util import Language_Util
from local_data_util import Local_Data_Util
from qadmin_dialog import QAdmin_Dialog
from qbinfile_dialog import QBinFile_Dialog
from qcom_dialog import ComSelectDialog
from qhelp_dialog import QMyHelpDialog
from upgrade_cell import Upgrade_Cell
from upgrade_logger import Upgrade_Logger
from upgrade_manager import Upgrade_Manager
from upgrade_qthread import Upgrade_QThread
from upgrade_status import Upgrade_Status
from view_main import Ui_main_view


class View_Main_Manager(object):
    # ui界面对象
    mView = Ui_main_view()
    mMainWindow: QMainWindow = None

    mTitles = ["tb_title_id", "tb_title_port", "tb_title_type", "tb_title_start_time",
               "tb_title_end_time", "tb_title_progress", "tb_title_status"]
    mCellValues = ["0", "None", "None", "None", "None", "None", "None"]
    mSeqId = 0
    mCurComId = 1
    mCurFileId = 2
    mStartTimeId = 3
    mEndTimeId = 4
    mProgressId = 5
    mBurnStateId = 6

    # 工具按钮对象
    m_icons_key = ["start", "stop", "quit", "file", "admin"]
    m_icons_key_id = ["tool_bar_start", "tool_bar_stop", "tool_bar_exit", "tool_bar_file", "tool_bar_admin"]
    mToolBarDict = {}

    # 资源锁 (UI日志显示时,需要按不同串口显示)
    ui_lock = threading.Lock()
    # 表格数据对象
    mModel: QStandardItemModel = None
    # 查询设备Q线程
    mQueryThread = None

    @classmethod
    def getView(cls):
        return View_Main_Manager.mView

    @classmethod
    def setMainWindow(cls, mainWnd: QMainWindow):
        cls.mMainWindow = mainWnd

    @classmethod
    def getInfoStyle(cls, sInfo):
        titleFormat = '<b><font color="#000000" size="4">{}</font></b>'
        return titleFormat.format(sInfo)

    @classmethod
    def getErrorStyle(cls, sInfo):
        titleFormat = '<b><font color="#FF0000" size="4">{}</font></b>'
        return titleFormat.format(sInfo)

    @classmethod
    def getProgressStyle(cls, sInfo):
        titleFormat = '<b><font color="#0000FF" size="4">{}</font></b>'
        return titleFormat.format(sInfo)

    @classmethod
    def getExceptStyle(cls, sInfo):
        titleFormat = '<b><font color="#FF0000" size="4">{}</font></b>'
        return titleFormat.format(sInfo)

    @classmethod
    def getSuccessStyle(cls, sInfo):
        titleFormat = '<b><font color="#00FF00" size="4">{}</font></b>'
        return titleFormat.format(sInfo)

    @classmethod
    def getDevInfoStyle(cls, sInfo: str, sColor: str):
        titleFormat = '<b><font color="%s" size="4">{}</font></b>' % sColor
        return titleFormat.format(sInfo)

    @classmethod
    def getStateInfoStyle(cls, upCell: Upgrade_Cell, sUpType: str, sState: str, isQuery: bool):
        # 正常升级结束状态
        if not isQuery:
            boTypeFound = False
            for i in range(len(upCell.mUpgradeTypeLst)):
                if upCell.mUpgradeTypeLst[i] == sUpType:
                    boTypeFound = True
                    break
            # 单个升级方式,其它类型的状态用默认颜色显示
            if not boTypeFound:
                return '<b><font color="#000000" size="4">{}</font></b>'.format(sState)
            if sState == Upgrade_Status.RLT_STATE_PASS:
                return '<b><font color="#00FF00" size="4">{}</font></b>'.format(sState)
            elif sState == Upgrade_Status.RLT_STATE_FAIL:
                return '<b><font color="#FF0000" size="4">{}</font></b>'.format(sState)
            else:
                return '<b><font color="#FFFF00" size="4">{}</font></b>'.format(sState)
        else:
            # 查询设备状态(默认颜色显示)
            return '<b><font color="#000000" size="4">{}</font></b>'.format(sState)

    @classmethod
    def addTextHintEx(cls, sText: str, dropDown: bool = False):
        wndMain = cls.getView()
        wndMain.edtMsg.append(sText)
        if dropDown:
            # 滑动到最低端显示
            hVerticalBar = wndMain.edtMsg.verticalScrollBar()
            if hVerticalBar:
                curValue = hVerticalBar.value()
                # minValue = hVerticalBar.minimum()
                maxValue = hVerticalBar.maximum()
                # print(f"cValue={curValue} minValue={minValue}, maxValue={maxValue}")
                if curValue < maxValue:
                    hVerticalBar.setValue(maxValue)

    @classmethod
    def onWindowCloseEvent(cls, event):
        if Upgrade_Manager.isUpgradeProcessing():
            info = Language_Util.getValue('wnd_close_tips')
            cls.showWarningInfo(info)
            event.ignore()
        else:
            if Device_QThread.mQuerying:
                info = Language_Util.getValue('wnd_close_query_tips')
                cls.showWarningInfo(info)
                event.ignore()
            else:
                event.accept()

    @classmethod
    def setCtxWidgets(cls):
        # 添加按键事件
        wndMain = cls.getView()
        # 设置垂直布局
        qvlayout = QtWidgets.QVBoxLayout(wndMain.centralwidget)

        wndMain.tblStateView = QtWidgets.QTableView()
        wndMain.tblStateView.setGeometry(QtCore.QRect(10, 22, 1001, 480))
        wndMain.tblStateView.setObjectName("tblStateView")

        wndMain.edtMsg = QtWidgets.QTextEdit()
        wndMain.edtMsg.setGeometry(QtCore.QRect(11, 260, 1001, 350))
        wndMain.edtMsg.setObjectName("edtMsg")

        qvlayout.addWidget(wndMain.tblStateView)
        qvlayout.addWidget(wndMain.edtMsg)
        # 设置布局伸缩性
        qvlayout.setStretch(0, 3)  # QTableView 占用空间
        qvlayout.setStretch(1, 4)  # QTextEdit 也占用空间

    @classmethod
    def showStatusInfo(cls):
        try:
            if not Local_Data_Util.fwSharedData["autoUpgrade"]:
                tmpValueNone = Language_Util.getValue("up_state_none")
                sComInfo = f"  {Language_Util.getValue('st_title_port_type')}:{tmpValueNone} "
                sFileInfo = f" {Language_Util.getValue('st_title_file_path')}:{tmpValueNone}"

                # 选择的串口
                tmpComInfo = Upgrade_Manager.getUpgradeComListInfo()
                if len(tmpComInfo) > 0:
                    sComInfo = f"  {Language_Util.getValue('st_title_serial_port')}:{tmpComInfo} "

                # 选择的文件路径
                tmpFilePath = Local_Data_Util.getUpgradeBinFileEx(Local_Data_Util.fwSharedData["sltType"])
                if len(tmpFilePath) > 0:
                    sFileInfo = f" {Language_Util.getValue('st_title_file_path')}:{tmpFilePath}"

                # 选择的升级类型
                if Local_Data_Util.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_BT:
                    sFileType = f" {Language_Util.getValue('st_title_upgrade_type')}:BT"
                elif Local_Data_Util.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_VOICE:
                    sFileType = f" {Language_Util.getValue('st_title_upgrade_type')}:Voice"
                else:
                    sFileType = f" {Language_Util.getValue('st_title_upgrade_type')}:Demo"

                sInfo = sComInfo + sFileType + sFileInfo
                cls.getView().lblStatus.setText(sInfo)
            else:
                tmpValueNone = Language_Util.getValue("up_state_none")
                sComInfo = f"  {Language_Util.getValue('st_title_port_type')}:{tmpValueNone} "
                sFileInfo = f" {Language_Util.getValue('st_title_file_path')}:{tmpValueNone}"

                # 选择的串口
                tmpComInfo = Upgrade_Manager.getUpgradeComListInfo()
                if len(tmpComInfo) > 0:
                    sComInfo = f"  {Language_Util.getValue('st_title_serial_port')}:{tmpComInfo} "

                # 选择的文件路径
                tmpBinList = [Local_Data_Util.fwSharedData["btPath"],
                              Local_Data_Util.fwSharedData["demoPath"],Local_Data_Util.fwSharedData["voicePath"]]
                tmpNameInfo = "  "
                tmpParentPath = ""
                tmpSize = len(tmpBinList)
                for i in range(tmpSize):
                    tmpFilePath = tmpBinList[i]
                    tmpFileName = ""
                    if len(tmpFilePath) > 0:
                        if len(tmpParentPath) == 0:
                            tmpParentPath = os.path.dirname(tmpFilePath) + "/"
                        tmpFileName = os.path.basename(tmpFilePath)
                    if i < tmpSize - 1:
                        tmpNameInfo += tmpFileName + ", "
                    else:
                        tmpNameInfo += tmpFileName
                if len(tmpParentPath) > 0:
                    sFileInfo = f" {Language_Util.getValue('st_title_file_path')}:{tmpParentPath}\n{tmpNameInfo}"

                sFileType = f" {Language_Util.getValue('st_title_upgrade_type')}:[BT,Demo,Voice]"

                sInfo = sComInfo + sFileType + sFileInfo
                cls.getView().lblStatus.setText(sInfo)
        except Exception as e:
            print("showStatusInfo error?" + repr(e))

    @classmethod
    def addBurnTypeSubMenu(cls):
        # 添加按键事件
        wndMain = cls.getView()

        # 创建一个QActionGroup对象
        group = QActionGroup(cls.mMainWindow)
        # 设置为True，确保只能选择一个
        group.setExclusive(True)

        # 创建两个QAction对象，它们属于同一个QActionGroup
        mnuCModel = QAction(f"{Language_Util.getValue('uptype_c_module')}", cls.mMainWindow, checkable=True)
        # 将QAction对象添加到QActionGroup
        group.addAction(mnuCModel)
        # 将QAction对象添加到菜单
        wndMain.mnuType.addAction(mnuCModel)

        # 只保留C模块升级类型(Python协议丢弃)
        mnuCModel.setChecked(True)

    @classmethod
    def onBinTypeBt(cls):
        if Local_Data_Util.fwSharedData["sltType"] != Local_Data_Util.FW_TYPE_BT:
            Local_Data_Util.fwSharedData["sltType"] = Local_Data_Util.FW_TYPE_BT
            Local_Data_Util.saveData()
        cls.showStatusInfo()

    @classmethod
    def onBinTypeVoice(cls):
        if Local_Data_Util.fwSharedData["sltType"] != Local_Data_Util.FW_TYPE_VOICE:
            Local_Data_Util.fwSharedData["sltType"] = Local_Data_Util.FW_TYPE_VOICE
            Local_Data_Util.saveData()
        cls.showStatusInfo()

    @classmethod
    def onBinTypeDemo(cls):
        if Local_Data_Util.fwSharedData["sltType"] != Local_Data_Util.FW_TYPE_DEMO:
            Local_Data_Util.fwSharedData["sltType"] = Local_Data_Util.FW_TYPE_DEMO
            Local_Data_Util.saveData()
        cls.showStatusInfo()

    @classmethod
    def onBinTypeAuto(cls, checked):
        if Local_Data_Util.fwSharedData["autoUpgrade"] != checked:
            Local_Data_Util.fwSharedData["autoUpgrade"] = checked
            Local_Data_Util.saveData()
            cls.showStatusInfo()

    @classmethod
    def onBinTypeStressUpgrade(cls, checked):
        if Local_Data_Util.fwSharedData["stressUpgrade"] != checked:
            Local_Data_Util.fwSharedData["stressUpgrade"] = checked
            Local_Data_Util.saveData()
            cls.showStatusInfo()

    @classmethod
    def addBinTypeSubMenu(cls):
        # 添加按键事件
        wndMain = cls.getView()

        # 创建一个QActionGroup对象
        group = QActionGroup(cls.mMainWindow)
        # 设置为True，确保只能选择一个
        group.setExclusive(True)

        # 创建三个QAction对象，它们属于同一个QActionGroup
        mnuBinBT = QAction(f"BT {Language_Util.getValue('mnu_type')}", cls.mMainWindow, checkable=True)
        # 将QAction对象添加到QActionGroup
        group.addAction(mnuBinBT)
        # 将QAction对象添加到菜单
        wndMain.mnuBinType.addAction(mnuBinBT)
        # 添加分隔符
        wndMain.mnuBinType.addSeparator()

        mnuBinVoice = QAction(f"Voice {Language_Util.getValue('mnu_type')}", cls.mMainWindow, checkable=True)
        group.addAction(mnuBinVoice)
        wndMain.mnuBinType.addAction(mnuBinVoice)
        # 添加分隔符
        wndMain.mnuBinType.addSeparator()

        mnuBinDemo = QAction(f"Demo {Language_Util.getValue('mnu_type')}", cls.mMainWindow, checkable=True)
        group.addAction(mnuBinDemo)
        wndMain.mnuBinType.addAction(mnuBinDemo)
        # 添加分隔符
        wndMain.mnuBinType.addSeparator()

        # 复选框 (自动升级方式: BT,DEMO,Voice类型按顺序升级)
        mnuBinAuto = QAction(f"{Language_Util.getValue('mnu_type_auto')}", cls.mMainWindow, checkable=True)
        wndMain.mnuBinType.addAction(mnuBinAuto)
        # 添加分隔符
        wndMain.mnuBinType.addSeparator()

        # 复选框 (强制升级,不比较版本号)
        mnuBinStress = QAction(f"{Language_Util.getValue('mnu_type_stress')}", cls.mMainWindow, checkable=True)
        wndMain.mnuBinType.addAction(mnuBinStress)

        # 添加事件
        mnuBinBT.triggered.connect(cls.onBinTypeBt)
        mnuBinVoice.triggered.connect(cls.onBinTypeVoice)
        mnuBinDemo.triggered.connect(cls.onBinTypeDemo)
        mnuBinAuto.triggered.connect(cls.onBinTypeAuto)
        mnuBinStress.triggered.connect(cls.onBinTypeStressUpgrade)

        # 设置默认选项
        if Local_Data_Util.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_BT:
            mnuBinBT.setChecked(True)
        elif Local_Data_Util.fwSharedData["sltType"] == Local_Data_Util.FW_TYPE_VOICE:
            mnuBinVoice.setChecked(True)
        else:
            mnuBinDemo.setChecked(True)

        # 复选框(选中状态)
        mnuBinAuto.setChecked(Local_Data_Util.fwSharedData["autoUpgrade"])
        mnuBinStress.setChecked(Local_Data_Util.fwSharedData["stressUpgrade"])

    @classmethod
    def addStatusLabel(cls):
        tmpView = cls.getView()
        tmpView.lblStatus = QLabel("")
        tmpView.lblStatus.setStyleSheet("color:blue")
        tmpView.statusbar.addWidget(tmpView.lblStatus)

    @classmethod
    def onActionLanguageSelect(cls):
        try:
            action = cls.mMainWindow.sender()
            tmpData = action.data()
            if tmpData == Local_Data_Util.fwSharedData['language']:
                return
            answer = QMessageBox.question(cls.mMainWindow,
                                          Language_Util.getValue("dlg_title_tips"),
                                          Language_Util.getValue("lang_tips"),
                                          QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.Yes:
                Local_Data_Util.fwSharedData['language'] = tmpData
                # 保存语言设置
                Local_Data_Util.saveData()

                # 关闭当前窗口
                cls.mMainWindow.close()
        except Exception as e:
            print("onActionLanguageSelect error?" + repr(e))

    @classmethod
    def addLanguageTypeSubMenu(cls):
        # 添加按键事件
        wndMain = cls.getView()

        # 创建一个QActionGroup对象
        group = QActionGroup(cls.mMainWindow)
        # 设置为True，确保只能选择一个
        group.setExclusive(True)

        mnuLangCn = QAction("简体中文", cls.mMainWindow, checkable=True)
        mnuLangCn.setData(Language_Util.CODE_CN)
        # 将QAction对象添加到QActionGroup
        group.addAction(mnuLangCn)
        # 将QAction对象添加到菜单
        wndMain.mnuLanguage.addAction(mnuLangCn)
        # 添加分隔符
        wndMain.mnuLanguage.addSeparator()

        mnuLangEn = QAction("English", cls.mMainWindow, checkable=True)
        mnuLangEn.setData(Language_Util.CODE_EN)
        # 将QAction对象添加到QActionGroup
        group.addAction(mnuLangEn)
        # 将QAction对象添加到菜单
        wndMain.mnuLanguage.addAction(mnuLangEn)
        # 添加分隔符
        wndMain.mnuLanguage.addSeparator()

        mnuLangKr = QAction("한국인", cls.mMainWindow, checkable=True)
        mnuLangKr.setData(Language_Util.CODE_KR)
        # 将QAction对象添加到QActionGroup
        group.addAction(mnuLangKr)
        # 将QAction对象添加到菜单
        wndMain.mnuLanguage.addAction(mnuLangKr)

        # 添加事件
        mnuLangCn.triggered.connect(cls.onActionLanguageSelect)
        mnuLangEn.triggered.connect(cls.onActionLanguageSelect)
        mnuLangKr.triggered.connect(cls.onActionLanguageSelect)

        # 设置默认选项
        if Local_Data_Util.fwSharedData["language"] == Language_Util.CODE_CN:
            mnuLangCn.setChecked(True)
        elif Local_Data_Util.fwSharedData["language"] == Language_Util.CODE_EN:
            mnuLangEn.setChecked(True)
        else:
            mnuLangKr.setChecked(True)

    @classmethod
    def refreshMenuInfoByLang(cls):
        wndMain = cls.getView()

        # 操作
        wndMain.mnuOp.setTitle(Language_Util.getValue("mnu_op"))
        wndMain.actionQuit.setText(Language_Util.getValue("mnu_op_exit"))
        # 配置
        wndMain.mnuSerial.setTitle(Language_Util.getValue("mnu_conf"))
        wndMain.actionList.setText(Language_Util.getValue("mnu_conf_port"))
        wndMain.actionBinFile.setText(f"{Language_Util.getValue('mnu_conf_file')}(bin)")
        # 协议
        wndMain.mnuType.setTitle(Language_Util.getValue("mnu_protocol"))
        # 类型
        wndMain.mnuBinType.setTitle(Language_Util.getValue("mnu_type"))
        # 查询
        wndMain.menuQueryDev.setTitle(Language_Util.getValue("mnu_query"))
        wndMain.actionQueryDevInfo.setText(Language_Util.getValue("mnu_query_dev"))
        # 语言
        wndMain.mnuLanguage.setTitle(Language_Util.getValue("mnu_lang"))
        # 关于
        wndMain.mnuAbout.setTitle(Language_Util.getValue("mnu_about"))
        wndMain.actionHelp.setText(Language_Util.getValue("mnu_about_help"))
        wndMain.actionVersion.setText(Language_Util.getValue("mnu_about_soft"))

    @classmethod
    def on_action_quit(cls):
        cls.mMainWindow.close()

    @classmethod
    def on_action_com_list(cls):
        # 创建并显示对话框
        dialog = ComSelectDialog()
        dialog.exec_()
        cls.showStatusInfo()

    @classmethod
    def on_action_fwfile_select(cls):
        # 每次选择bin文件都要授权验证(防止误操作)
        dialog = QAdmin_Dialog()
        dialog.setCallBack(cls.do_open_binfile_dialog_event)
        dialog.exec_()

    @classmethod
    def on_action_help_select(cls):
        dialog = QMyHelpDialog()
        dialog.exec_()

    @classmethod
    def showWarningInfo(cls, info):
        wndMain = cls.mView
        wndMain.mWarning = QMessageBox(QMessageBox.Warning, f"{Language_Util.getValue('dlg_title_warn')}", info)
        wndMain.mWarning.setWindowIcon(Config_Data.MAIN_ICON)
        wndMain.mWarning.show()

    @classmethod
    def showInformationInfo(cls, info):
        wndMain = cls.mView
        wndMain.mWarning = QMessageBox(QMessageBox.Information, f"{Language_Util.getValue('dlg_title_tips')}", info)
        wndMain.mWarning.setWindowIcon(Config_Data.MAIN_ICON)
        wndMain.mWarning.show()

    @classmethod
    def on_action_version(cls):
        strVersion = f"1.{Language_Util.getValue('cur_ver')}:{Config_Data.TOOL_VERSION} \n " \
                     f"2.{Language_Util.getValue('suggest_contact')}\n xielunguo@cosonic.net"
        cls.showInformationInfo(strVersion)

    @classmethod
    def on_action_query_dev_info(cls):
        if Upgrade_Manager.getUpgradeCount() == 0:
            cls.showWarningInfo(f"{Language_Util.getValue('select_com_type')}")
            return

        # 防止重复点击
        cls.mToolBarDict["start"].setEnabled(False)
        cls.mToolBarDict["file"].setEnabled(False)
        cls.mToolBarDict["admin"].setEnabled(False)
        # 禁用菜单项(防止误操作)
        cls.enableMenuTypeButtons(False)

        # 警告,这里不能用局部变量(虚拟机会释放Q线程资源,会导致不可预测的异常)
        cls.mQueryThread = Device_QThread()
        cls.mQueryThread.call_fun_signal.connect(cls.solveUiProcess)
        cls.mQueryThread.start()

    @classmethod
    def do_query_end(cls):
        cls.mToolBarDict["start"].setEnabled(True)
        cls.mToolBarDict["file"].setEnabled(True)
        cls.mToolBarDict["admin"].setEnabled(True)
        cls.enableMenuTypeButtons(True)

        cls.mQueryThread = None

    @classmethod
    def addMenuTypeClickEvent(cls):
        # 添加按键事件
        wndMain = cls.getView()

        wndMain.actionQuit.triggered.connect(cls.on_action_quit)
        wndMain.actionList.triggered.connect(cls.on_action_com_list)
        wndMain.actionBinFile.triggered.connect(cls.on_action_fwfile_select)
        wndMain.actionHelp.triggered.connect(cls.on_action_help_select)
        wndMain.actionVersion.triggered.connect(cls.on_action_version)
        wndMain.actionQueryDevInfo.triggered.connect(cls.on_action_query_dev_info)

    @classmethod
    def setTableViewConfig(cls):
        # 添加按键事件
        wndMain = cls.getView()

        # 清空消息日志
        wndMain.edtMsg.setText("")

        max_row = 1 + Config_Data.MAX_C_MODULE_COUNT
        max_col = len(cls.mTitles)
        cls.mModel = QStandardItemModel(max_row, max_col)
        for tmpCol in range(0, max_col):
            cls.mModel.setItem(0, tmpCol, QStandardItem(Language_Util.getValue(cls.mTitles[tmpCol])))
        # 将 None值,修改为三种语言格式的
        tmpValueNone = Language_Util.getValue("up_state_none")
        for tmpCol in range(0, max_col):
            if tmpCol > 0:
                cls.mModel.setItem(1, tmpCol, QStandardItem(tmpValueNone))
            else:
                cls.mModel.setItem(1, tmpCol, QStandardItem(cls.mCellValues[tmpCol]))

        wndMain.tblStateView.setModel(cls.mModel)
        # 标题高亮显示
        for i in range(max_col):
            # 设置标题加粗显示
            tmpItem = cls.mModel.item(0, i)
            # 设置字体颜色
            tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
            # 设置字体加粗
            tmpItem.setFont(QFont("Times", 12, QFont.Black))
            # 设置背景颜色
            tmpItem.setBackground(QBrush(QColor(0, 200, 0)))

        # 设置状态列显示的宽度(英文,韩语,状态显示不合理)
        wndMain.tblStateView.setColumnWidth(max_col - 1, 280)

        # 设置自定义的委托(目的:单元格居中显示)
        delegate = CenterDelegate()
        wndMain.tblStateView.setItemDelegate(delegate)

    @classmethod
    def enableMenuTypeButtons(cls, enabled: bool):
        wndMain = cls.getView()
        # 配置
        wndMain.mnuSerial.setEnabled(enabled)
        # 协议
        wndMain.mnuType.setEnabled(enabled)
        # 类型
        wndMain.mnuBinType.setEnabled(enabled)
        # 查询
        wndMain.menuQueryDev.setEnabled(enabled)
        # 语言
        wndMain.mnuLanguage.setEnabled(enabled)

    @classmethod
    def clearTableViewCtx(cls, upgradeCnt: int):
        max_row = 1 + Config_Data.MAX_C_MODULE_COUNT
        max_col = len(cls.mTitles)
        try:
            # 清空单元格
            for tmpRow in range(1, max_row):
                for tmpCol in range(max_col):
                    tmpIndex = cls.mModel.index(tmpRow, tmpCol)
                    cls.mModel.setData(tmpIndex, "")
                    if (tmpCol == cls.mProgressId) or (tmpCol == cls.mBurnStateId):
                        tmpItem = cls.mModel.item(tmpRow, tmpCol)
                        tmpItem.setBackground(QBrush(QColor(255, 255, 255)))
        except Exception as e:
            print("clearTableViewCtx error?",repr(e))

    @classmethod
    def update_cmodule_wait(cls, index: int, secs: int):
        try:
            tmpIndex = cls.mModel.index(index, cls.mBurnStateId)
            cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_waiting')}({secs})s")
        except Exception as e:
            print(f"[{index}] update_cmodule_wait error?" + repr(e))

    @classmethod
    def update_state_value(cls, upCell: Upgrade_Cell, index: int, bsState: int):
        try:
            tmpIndex = cls.mModel.index(index, cls.mBurnStateId)

            if upCell.mUpgradeState == Upgrade_Status.BS_FREE:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_idle')}...")
            elif upCell.mUpgradeState == Upgrade_Status.BS_REQUEST_SYNC:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_request')}...")
            elif upCell.mUpgradeState == Upgrade_Status.BS_DATA_TRANSFER:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_data_transfer')}...")
            elif upCell.mUpgradeState == Upgrade_Status.BS_DATA_TRANSFER_END:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_transfer_end')}...")
            elif upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_SUCCESS:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_success')}...")
            elif upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_ERROR:
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_failed')}...")
        except Exception as e:
            print(f"[{index}] update_state_value error?" + repr(e))

    @classmethod
    def update_progress_value(cls, index: int, progress: int):
        try:
            # 当前进度
            tmpIndex = cls.mModel.index(index, cls.mProgressId)
            cls.mModel.setData(tmpIndex, "%d%%" % progress)
        except Exception as e:
            print(f"[{index}] update_progress_value error?" + repr(e))

    @classmethod
    def upgrade_end(cls, upCell: Upgrade_Cell):
        try:
            # 日志信息与显示UI(需要加锁操作)
            cls.ui_lock.acquire()

            # 标记升级结果状态
            if upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_SUCCESS:
                upCell.mUpgradeResult[upCell.mUpgradeIndex] = Upgrade_Status.RLT_STATE_PASS
            else:
                if upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_IGNORE:
                    upCell.mUpgradeResult[upCell.mUpgradeIndex] = Upgrade_Status.RLT_STATE_IGNORE
                else:
                    upCell.mUpgradeResult[upCell.mUpgradeIndex] = Upgrade_Status.RLT_STATE_FAIL

            # 如果整个升级逻辑处理完成后,需要更新版本号(因为最后一个类型升级成功后,不会查询设备版本号)
            # 目的:实现保存文件中的版本号与设备同步
            if upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_SUCCESS:
                if upCell.mUpgradeIndex == len(upCell.mUpgradeTypeLst) - 1:
                    upCell.refreshVersionByFilename()

            # 更新状态显示
            if upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_SUCCESS:
                tmpIndex = cls.mModel.index(upCell.mIndex, cls.mBurnStateId)
                cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_success')}...")
                tmpItem = cls.mModel.item(upCell.mIndex, cls.mBurnStateId)
                tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
                tmpItem.setFont(QFont("Times", 12, QFont.Black))
                tmpItem.setBackground(QBrush(QColor(0, 255, 0)))
            else:
                tmpIndex = cls.mModel.index(upCell.mIndex, cls.mBurnStateId)
                if upCell.mUpgradeState == Upgrade_Status.BS_UPGRADE_IGNORE:
                    cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_ignore')}...")
                    tmpItem = cls.mModel.item(upCell.mIndex, cls.mBurnStateId)
                    tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
                    tmpItem.setFont(QFont("Times", 12, QFont.Black))
                    tmpItem.setBackground(QBrush(QColor(255, 255, 0)))
                else:
                    cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_failed')}...")
                    tmpItem = cls.mModel.item(upCell.mIndex, cls.mBurnStateId)
                    tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
                    tmpItem.setFont(QFont("Times", 12, QFont.Black))
                    tmpItem.setBackground(QBrush(QColor(255, 0, 0)))

            # 更新结束时间
            sTimeInfo = time.strftime("%H:%M:%S", time.localtime())
            tmpIndex = cls.mModel.index(upCell.mIndex, cls.mEndTimeId)
            cls.mModel.setData(tmpIndex, sTimeInfo)
            upCell.mEndTime = sTimeInfo

            span_info = "-" * 20
            tmpStrSeqId = f"{Language_Util.getValue(cls.mTitles[cls.mSeqId])}:{upCell.mIndex}"
            tmpStrComId = f"{Language_Util.getValue(cls.mTitles[cls.mCurComId])}:{upCell.mComNum}"
            tmpStrTypeId = f"{Language_Util.getValue(cls.mTitles[cls.mCurFileId])}:{upCell.mUpgradeTypeLst[upCell.mUpgradeIndex]}"
            info_title_start = span_info + f" [{tmpStrSeqId},{tmpStrComId},{tmpStrTypeId}] " + span_info
            info_title_end = span_info + " [end] " + span_info

            # 输出日志
            console_logs = Upgrade_Logger.getConsoleLogByIndex(upCell.mIndex)
            for tmpLine in console_logs:
                print(f"[{upCell.mIndex}] {tmpLine}")

            # 输出内容(内容组件上)
            table_logs = Upgrade_Logger.getTableLogByIndex(upCell.mIndex)
            if len(table_logs) > 0:
                cls.addTextHintEx("", False)
                cls.addTextHintEx(cls.getInfoStyle(info_title_start), False)
                for tmpLine in table_logs:
                    cls.addTextHintEx(tmpLine, False)
                cls.addTextHintEx(cls.getInfoStyle(info_title_end), True)
        except Exception as e:
            print(f"[{upCell.mIndex}] upgrade_end error?" + repr(e))
        finally:
            # 清空日志记录
            Upgrade_Logger.clearConsoleLogByIndex(upCell.mIndex)
            Upgrade_Logger.clearTableLogByIndex(upCell.mIndex)
            # 防止Q线程遇到异常后,关闭不掉状态,导致的超时等待
            upCell.mUpgrading = False
            # 释放锁
            if cls.ui_lock.locked():
                cls.ui_lock.release()

    @classmethod
    def upgrade_process_end(cls, upCell: Upgrade_Cell):
        try:
            cls.ui_lock.acquire()

            # 只有所有升级单元对象都升级完成后,才能恢复所有功能选项
            if not Upgrade_Manager.isUpgradeProcessing():
                # 恢复菜单项(可点击)
                cls.enableMenuTypeButtons(True)
                # 可重新开始烧入
                cls.mToolBarDict["start"].setEnabled(True)
                cls.mToolBarDict["file"].setEnabled(True)
                cls.mToolBarDict["admin"].setEnabled(True)

            # 保存升级记录到地文件文件(自动升级方式,直接保存数据,不需要更新数据)
            if upCell.mUpgradeIndex > 0:
                csvFile = Device_Csv_Util.getFileName()
                tmpMac = upCell.mMacAddress
                tmpVer = upCell.mVersion

                tmpBtIndex = Device_Filepath_Util.find_index_by_filepath(upCell.mUpgradeBinLst[0])
                tmpBtValue = f"{tmpBtIndex}#{upCell.mUpgradeResult[0]}"

                tmpDemoIndex = Device_Filepath_Util.find_index_by_filepath(upCell.mUpgradeBinLst[1])
                tmpDemoValue = f"{tmpDemoIndex}#{upCell.mUpgradeResult[1]}"

                tmpVoiceIndex = Device_Filepath_Util.find_index_by_filepath(upCell.mUpgradeBinLst[2])
                tmpVoiceValue = f"{tmpVoiceIndex}#{upCell.mUpgradeResult[2]}"

                tmpNewRecord = Device_Csv_Util.add_or_update_record(csvFile, tmpMac, tmpVer, tmpBtValue,
                                                                    tmpVoiceValue, tmpDemoValue)
            else:
                csvFile = Device_Csv_Util.getFileName()
                tmpMac = upCell.mMacAddress
                tmpVer = upCell.mVersion

                tmpRecord = Device_Csv_Util.find_record_by_mac(csvFile, tmpMac)
                tmpBtValue = f"0#{Upgrade_Status.RLT_STATE_NONE}"
                tmpVoiceValue = f"0#{Upgrade_Status.RLT_STATE_NONE}"
                tmpDemoValue = f"0#{Upgrade_Status.RLT_STATE_NONE}"
                if tmpRecord is not None:
                    tmpBtValue = tmpRecord["BT"]
                    tmpVoiceValue = tmpRecord["Voice"]
                    tmpDemoValue = tmpRecord["Demo"]

                tmpBinIndex = Device_Filepath_Util.find_index_by_filepath(upCell.mUpgradeBinLst[0])
                if upCell.mUpgradeTypeLst[0] == Local_Data_Util.FW_TYPE_BT:
                    tmpBtValue = f"{tmpBinIndex}#{upCell.mUpgradeResult[0]}"
                elif upCell.mUpgradeTypeLst[0] == Local_Data_Util.FW_TYPE_VOICE:
                    tmpVoiceValue = f"{tmpBinIndex}#{upCell.mUpgradeResult[0]}"
                else:
                    tmpDemoValue = f"{tmpBinIndex}#{upCell.mUpgradeResult[0]}"
                tmpNewRecord = Device_Csv_Util.add_or_update_record(csvFile, tmpMac, tmpVer,
                                                                    tmpBtValue, tmpVoiceValue, tmpDemoValue)
            # 如果是自动升级方式,则显示三种结果状态
            if upCell.mUpgradeIndex > 0:
                cls.show_process_result_info(upCell)
            # 显示升级结果状态
            cls.show_record_info(upCell, tmpNewRecord, False)
        except Exception as e:
            print(f"[{upCell.mIndex}] upgrade_process_end error?" + repr(e))
        finally:
            cls.ui_lock.release()

    @classmethod
    def show_process_result_info(cls, upCell: Upgrade_Cell):
        try:
            tmpRow = upCell.mIndex
            # 烧入类型
            tmpIndex = cls.mModel.index(tmpRow, cls.mCurFileId)
            cls.mModel.setData(tmpIndex, "bt,demo,voice")

            # 开始时间
            tmpIndex = cls.mModel.index(tmpRow, cls.mStartTimeId)
            cls.mModel.setData(tmpIndex, upCell.mProcessStartTime)

            # 结束时间
            tmpIndex = cls.mModel.index(tmpRow, cls.mEndTimeId)
            cls.mModel.setData(tmpIndex, upCell.mProcessEndTime)

            tmpRltCnt = len(upCell.mUpgradeResult)
            sucCnt = 0
            for i in range(tmpRltCnt):
                if upCell.mUpgradeResult[i] == Upgrade_Status.RLT_STATE_PASS:
                    sucCnt += 1
            # 结果状态
            rltStatus = f"{upCell.mUpgradeResult[0]},{upCell.mUpgradeResult[1]},{upCell.mUpgradeResult[2]}"
            tmpIndex = cls.mModel.index(tmpRow, cls.mBurnStateId)
            cls.mModel.setData(tmpIndex, rltStatus)
            tmpItem = cls.mModel.item(tmpRow, cls.mBurnStateId)
            tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
            tmpItem.setFont(QFont("Times", 12, QFont.Black))
            # 全部类型升级成功与部分成功,显示不同的颜色
            if sucCnt == tmpRltCnt:
                tmpItem.setBackground(QBrush(QColor(0, 255, 0)))
            elif sucCnt == 0:
                tmpItem.setBackground(QBrush(QColor(255, 0, 0)))
            else:
                tmpItem.setBackground(QBrush(QColor(255, 255, 0)))
        except Exception as e:
            print(f"[{upCell.mIndex}] show_process_status_info error?" + repr(e))

    @classmethod
    def show_record_info(cls, upCell: Upgrade_Cell, record: dict, isQuery: bool = False):
        try:
            span_info = "-" * 20
            tmpStrSeqId = f"{Language_Util.getValue(cls.mTitles[cls.mSeqId])}:{upCell.mIndex}"
            tmpStrComId = f"{Language_Util.getValue(cls.mTitles[cls.mCurComId])}:{upCell.mComNum}"
            info_title_start = span_info + f" [{tmpStrSeqId},{tmpStrComId}] " + span_info
            info_title_end = span_info + " [end] " + span_info

            # 设备信息
            lineDeviceInfoTitle = f"{Language_Util.getValue('dev_info')}"
            allVer = record["Version"].split("#")
            lineVer = f"{Language_Util.getValue('dev_version')}" + f" BT={allVer[0]} Voice={allVer[1]} Demo={allVer[2]}"
            lineMac = f"{Language_Util.getValue('dev_mac')}" + record["Mac"]
            lineOpTime = f"{Language_Util.getValue('dev_info_last_upgrade')}:{record['OpTime']}"

            # 升级类型-状态-文件路径
            ctSpan = 8
            csSpan = 8
            cfSpan = 64
            cFill = "-"
            lineCsvInfoTitle = f"{Language_Util.getValue('dev_type').center(ctSpan, cFill)}|"
            lineCsvInfoTitle += f"{Language_Util.getValue('dev_status').center(csSpan, cFill)}|"
            lineCsvInfoTitle += f"{Language_Util.getValue('dev_file').center(cfSpan, cFill)}"

            # 每个类型状态信息
            tmpStates = record["BT"].split("#")
            tmpBinFile = Device_Filepath_Util.find_filepath_by_index(int(tmpStates[0]))
            tmpTypeValue = "BT".center(ctSpan, cFill)
            tmpStateValue = tmpStates[1].center(csSpan, cFill)
            tmpStateStyle = cls.getStateInfoStyle(upCell, Local_Data_Util.FW_TYPE_BT, tmpStates[1], isQuery)
            tmpStateValue = tmpStateValue.replace(tmpStates[1], tmpStateStyle)
            tmpFileValue = tmpBinFile.center(cfSpan, cFill)
            lineStateBt = f"{tmpTypeValue}|{tmpStateValue}|{tmpFileValue}"

            tmpStates = record["Voice"].split("#")
            tmpBinFile = Device_Filepath_Util.find_filepath_by_index(int(tmpStates[0]))
            tmpTypeValue = "Voice".center(ctSpan, cFill)
            tmpStateValue = tmpStates[1].center(csSpan, cFill)
            tmpStateStyle = cls.getStateInfoStyle(upCell, Local_Data_Util.FW_TYPE_VOICE, tmpStates[1], isQuery)
            tmpStateValue = tmpStateValue.replace(tmpStates[1], tmpStateStyle)
            tmpFileValue = tmpBinFile.center(cfSpan, cFill)
            lineStateVoice = f"{tmpTypeValue}|{tmpStateValue}|{tmpFileValue}"

            tmpStates = record["Demo"].split("#")
            tmpBinFile = Device_Filepath_Util.find_filepath_by_index(int(tmpStates[0]))
            tmpTypeValue = "Demo".center(ctSpan, cFill)
            tmpStateValue = tmpStates[1].center(csSpan, cFill)
            tmpStateStyle = cls.getStateInfoStyle(upCell, Local_Data_Util.FW_TYPE_DEMO, tmpStates[1], isQuery)
            tmpStateValue = tmpStateValue.replace(tmpStates[1], tmpStateStyle)
            tmpFileValue = tmpBinFile.center(cfSpan, cFill)
            lineStateDemo = f"{tmpTypeValue}|{tmpStateValue}|{tmpFileValue}"

            # 显示信息
            sTagColor = "#00AA00"
            sCtxColor = "#000000"
            cls.addTextHintEx("")
            cls.addTextHintEx(cls.getDevInfoStyle(info_title_start, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineDeviceInfoTitle, sTagColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineVer, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineMac, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineOpTime, sCtxColor))

            cls.addTextHintEx(cls.getDevInfoStyle(lineCsvInfoTitle, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineStateBt, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineStateVoice, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(lineStateDemo, sCtxColor))
            cls.addTextHintEx(cls.getDevInfoStyle(info_title_end, sCtxColor), True)
        except Exception as e:
            print(f"[{upCell.mIndex}] show_record_info error?" + repr(e))

    @classmethod
    def upgrade_type_start_event(cls, upCell: Upgrade_Cell):
        try:
            tmpRow = upCell.mIndex

            # 串口编号显示
            tmpIndex = cls.mModel.index(tmpRow, cls.mSeqId)
            sNumber = upCell.mIndex
            cls.mModel.setData(tmpIndex, sNumber)

            # 串口号
            tmpIndex = cls.mModel.index(tmpRow, cls.mCurComId)
            cls.mModel.setData(tmpIndex, upCell.mComNum)

            # 烧入类型
            tmpIndex = cls.mModel.index(tmpRow, cls.mCurFileId)
            curGradeType = upCell.mUpgradeTypeLst[upCell.mUpgradeIndex]
            cls.mModel.setData(tmpIndex, curGradeType)

            # 开始时间
            sTimeInfo = time.strftime("%H:%M:%S", time.localtime())
            # 记录开始时间
            upCell.mStartTime = sTimeInfo
            tmpIndex = cls.mModel.index(tmpRow, cls.mStartTimeId)
            cls.mModel.setData(tmpIndex, sTimeInfo)

            # 结束时间
            tmpIndex = cls.mModel.index(tmpRow, cls.mEndTimeId)
            cls.mModel.setData(tmpIndex, Language_Util.getValue("up_state_none"))

            # 当前进度
            tmpIndex = cls.mModel.index(tmpRow, cls.mProgressId)
            cls.mModel.setData(tmpIndex, "0%")
            # 设置背景颜色(当前进度)
            tmpItem = cls.mModel.item(tmpRow, cls.mProgressId)
            # 设置显示颜色
            tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
            # 设置字体加粗和颜色
            tmpItem.setFont(QFont("Times", 12, QFont.Black))
            # 设置背景颜色
            tmpItem.setBackground(QBrush(QColor(255, 255, 0)))

            # 当前状态
            tmpIndex = cls.mModel.index(tmpRow, cls.mBurnStateId)
            cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('ups_start')}...")
            tmpItem = cls.mModel.item(tmpRow, cls.mBurnStateId)
            tmpItem.setForeground(QBrush(QColor(0, 0, 0)))
            tmpItem.setFont(QFont("Times", 12, QFont.Black))
            tmpItem.setBackground(QBrush(QColor(255, 255, 0)))
        except Exception as e:
            print(f"[{upCell.mIndex}] upgrade_type_start_event error?" + repr(e))

    @classmethod
    def showDevInfoStateSecs(cls, index: int, secs: int):
        try:
            tmpIndex = cls.mModel.index(index, cls.mBurnStateId)
            cls.mModel.setData(tmpIndex, f"{Language_Util.getValue('up_state_dev_info_secs')}({secs})s")
        except Exception as e:
            print(f"[{index}] update_cmodule_wait error?" + repr(e))

    @classmethod
    def addDevInfoToTable(cls, index: int, ver: str, mac: str):
        try:
            lineDeviceInfoTitle = f"{Language_Util.getValue('dev_info')}"

            allVer = ver.split("#")
            lineVer = f"{Language_Util.getValue('dev_version')}" + f" BT={allVer[0]} Voice={allVer[1]} Demo={allVer[2]}"
            lineMac = f"{Language_Util.getValue('dev_mac')}" + mac

            sTagColor = "#00AA00"
            sCtxColor = "#000000"
            sText = cls.getDevInfoStyle(lineDeviceInfoTitle, sTagColor)
            Upgrade_Logger.addTableLog(index, sText)
            sText = cls.getDevInfoStyle(lineVer, sCtxColor)
            Upgrade_Logger.addTableLog(index, sText)
            sText = cls.getDevInfoStyle(lineMac, sCtxColor)
            Upgrade_Logger.addTableLog(index, sText)
        except Exception as e:
            print(f"[{index}] showDevInfo error" + repr(e))

    @classmethod
    def solveUiProcess(cls, index: int, fname: str, params: list):
        tmpCell = Upgrade_Manager.getUpgradeCellByIndex(index)
        try:
            if fname == Upgrade_Status.SI_TAG_UPGRADE_START:
                cls.upgrade_type_start_event(tmpCell)
            elif fname == Upgrade_Status.SI_TAG_DEV_INFO_SECS:
                cls.showDevInfoStateSecs(index, params[0])
            elif fname == Upgrade_Status.SI_TAG_DEV_INFO_RLT:
                cls.addDevInfoToTable(index, params[0], params[1])
            elif fname == Upgrade_Status.SI_TAG_INFO:
                sText = cls.getInfoStyle(params[0])
                Upgrade_Logger.addTableLog(index, sText)
            elif fname == Upgrade_Status.SI_TAG_ERROR:
                sText = cls.getErrorStyle(params[0])
                Upgrade_Logger.addTableLog(index, sText)
            elif fname == Upgrade_Status.SI_TAG_EXCEPT:
                sText = cls.getExceptStyle(params[0])
                Upgrade_Logger.addTableLog(index, sText)
            elif fname == Upgrade_Status.SI_TAG_COPEN:
                tmpCell.mCModuleProxy.startUpgrade()
            elif fname == Upgrade_Status.SI_TAG_CMODULE_WAIT:
                cls.update_cmodule_wait(index, params[0])
            elif fname == Upgrade_Status.SI_TAG_CHSTATE:
                cls.update_state_value(tmpCell, index, params[0])
            elif fname == Upgrade_Status.SI_TAG_PROGRESS:
                cls.update_progress_value(index, tmpCell.mUpgradeProgress)
            elif fname == Upgrade_Status.SI_TAG_END:
                cls.upgrade_end(tmpCell)
            elif fname == Upgrade_Status.SI_TAG_PROCESS_END:
                cls.upgrade_process_end(tmpCell)
            elif fname == Upgrade_Status.SI_TAG_QUERY_INFO:
                cls.show_record_info(tmpCell, params[1], True)
            elif fname == Upgrade_Status.SI_TAG_QUERY_END:
                cls.do_query_end()
        except Exception as e:
            print(f"[{index}] solveUiProcess error?" + repr(e))

    @classmethod
    def on_upgrade_start(cls):
        wndMain = cls.getView()

        upgradeCnt = Upgrade_Manager.getUpgradeCount()
        if upgradeCnt <= 0:
            cls.showWarningInfo(f"{Language_Util.getValue('select_com_type')}")
            return

        if not Local_Data_Util.checkBinPath():
            cls.showWarningInfo(f"{Language_Util.getValue('select_fw_file')}")
            return

        # 清空内容
        wndMain.edtMsg.setText("")
        # 清空控制台记录
        os.system("cls")
        # 进度清零
        wndMain.edtMsg.setText("")
        # 表格控制显示清空
        cls.clearTableViewCtx(upgradeCnt)
        # 日志记录清空
        Upgrade_Logger.clearAll()

        # 防止重复点击
        cls.mToolBarDict["start"].setEnabled(False)
        cls.mToolBarDict["file"].setEnabled(False)
        cls.mToolBarDict["admin"].setEnabled(False)
        # 禁用菜单项(防止误操作)
        cls.enableMenuTypeButtons(False)

        # 创建升级线程
        for tmpCell in Upgrade_Manager.mCells:
            tmpCell.mObserver = cls

            tmpQThread = Upgrade_QThread(tmpCell)
            tmpQThread.call_fun_signal.connect(cls.solveUiProcess)
            tmpCell.mUpgradeThread = tmpQThread
            tmpCell.mUpgradeThread.start()

    @classmethod
    def on_binfile_result_event(cls):
        cls.showStatusInfo()

    @classmethod
    def do_open_binfile_dialog_event(cls):
        dialog = QBinFile_Dialog()
        dialog.setParentWindow(cls.mMainWindow)
        dialog.setCallBack(cls.on_binfile_result_event)
        dialog.exec_()

    @classmethod
    def on_tool_bar_event(cls):
        action = cls.mMainWindow.sender()
        # 这里支持多种语言后,不能通过text值判断了。需要赋值data对象来判断是哪个按钮了点击了
        # sText = action.text()
        sText = action.data()
        if sText == "start":
            cls.on_upgrade_start()
        elif sText == "stop":
            pass
        elif sText == "quit":
            cls.mMainWindow.close()
        elif sText == "file":
            cls.on_action_com_list()
        elif sText == "admin":
            # 每次选择bin文件都要验证(防止误操作)
            dialog = QAdmin_Dialog()
            dialog.setCallBack(cls.do_open_binfile_dialog_event)
            dialog.exec_()

    @classmethod
    def initToolbar(cls):
        wndMain = cls.getView()

        # 创建动作(图标按钮)
        for i in range(len(cls.m_icons_key)):
            tmpFile = "./resources/%s_0.png" % (cls.m_icons_key[i])
            tmp_action = QAction(QIcon(tmpFile), Language_Util.getValue(cls.m_icons_key_id[i]), cls.mMainWindow)
            tmp_action.setData(cls.m_icons_key[i])
            wndMain.toolBar.addAction(tmp_action)
            tmp_action.triggered.connect(cls.on_tool_bar_event)
            cls.mToolBarDict[cls.m_icons_key[i]] = tmp_action

        # 设置按钮之间的间距
        styleSheet = """QToolBar {spacing: 5px;}"""
        wndMain.toolBar.setStyleSheet(styleSheet)

        # 禁止工具栏的浮动功能
        wndMain.toolBar.setFloatable(False)
        wndMain.toolBar.setMovable(False)
        # stop功能禁用
        cls.mToolBarDict["stop"].setEnabled(False)

    # 初始化按钮事件
    @classmethod
    def initEvents(cls):
        # 加载缓存数据
        Device_Filepath_Util.re_load_data()

        # 清除升级对象数据
        Upgrade_Manager.clearAll()

        # 中间内容(表格控件和消息内容显示)
        cls.setCtxWidgets()

        # 升级模块选择(C模块类型)
        cls.addBurnTypeSubMenu()

        # 升级类型选择(BT,VOICE,DEMO)
        cls.addBinTypeSubMenu()

        # 语言类型选择
        cls.addLanguageTypeSubMenu()

        #  状态栏类型选择
        cls.addStatusLabel()

        # 刷新语言显示
        cls.refreshMenuInfoByLang()

        # 菜单选项点击事件
        cls.addMenuTypeClickEvent()

        # 设置表格控件属性
        cls.setTableViewConfig()

        # 初始化工具栏按钮
        cls.initToolbar()

        # 显示本地加载的默认路径(bin文件)
        cls.showStatusInfo()

