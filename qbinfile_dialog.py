# -*- coding: UTF-8 -*-
# @Time    : 2024/9/27 10:32
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : qbinfile_dialog.py
# @IDE     : PyCharm
import os
import re

from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
from config_data import Config_Data
from device_filepath_util import Device_Filepath_Util
from dialog_binfile import Ui_dlgBinFile
from language_util import Language_Util
from local_data_util import Local_Data_Util


class QBinFile_Dialog(QDialog):
    def __init__(self):
        super().__init__()

        # 授权成功后,是否需要回调事件
        self.call_back_fun = None
        # 父类窗口对象(用于显示对话框)
        self.mParentWindow = None

        uiBinFile = Ui_dlgBinFile()
        uiBinFile.setupUi(self)
        self.uiBinFile = uiBinFile
        self.setWindowIcon(Config_Data.MAIN_ICON)

        self.setWindowTitle(Language_Util.getValue("dlg_fw_title"))
        # 设置对话框大小不可调节
        self.setFixedSize(692, 315)

        uiBinFile.lbl_tips.setText(f"{Language_Util.getValue('dlg_fw_tips')}(*.bin):")
        uiBinFile.lblBt.setText(f"B T {Language_Util.getValue('dlg_fw_type')}:")
        uiBinFile.lblVoice.setText(f"Voice {Language_Util.getValue('dlg_fw_type')}:")
        uiBinFile.lblDemo.setText(f"Demo {Language_Util.getValue('dlg_fw_type')}:")
        uiBinFile.btnOK.setText(Language_Util.getValue("dlg_fw_confirm"))
        uiBinFile.btnCancel.setText(Language_Util.getValue("dlg_fw_cancel"))

        # 居中显示
        desktop = QApplication.desktop()
        tmpRect = self.geometry()
        tmpX = (desktop.width() - tmpRect.width()) // 2 - 200
        tmpY = (desktop.height() - tmpRect.height()) // 2
        self.move(int(tmpX), int(tmpY))

        uiBinFile.btnOK.clicked.connect(self.on_ok_event)
        uiBinFile.btnCancel.clicked.connect(self.on_cancel_event)

        uiBinFile.btnBtType.clicked.connect(self.on_bt_select_event)
        uiBinFile.btnVoiceType.clicked.connect(self.on_voice_select_event)
        uiBinFile.btnDemoType.clicked.connect(self.on_demo_select_event)

        # 设置上次选择的文件路径
        uiBinFile.edtBtType.setText(Local_Data_Util.fwSharedData["btPath"])
        uiBinFile.edtVoiceType.setText(Local_Data_Util.fwSharedData["voicePath"])
        uiBinFile.edtDemoType.setText(Local_Data_Util.fwSharedData["demoPath"])

        # 克隆数据(用于验证是否需要保存数据
        self.mSharedData = Local_Data_Util.fwSharedData.copy()

    def on_bt_select_event(self):
        # 打开文件选择对话框，并只允许选择 .bin 文件
        file_path, _ = QFileDialog.getOpenFileName(self.mParentWindow,
                                                   Language_Util.getValue("dlg_fw_select_file"),
                                                   "", "BIN Files (*.bin)")
        if file_path:
            fileName = os.path.basename(file_path)
            matchObj = re.match(Config_Data.BIN_FILE_REGEX_BT, fileName)
            if matchObj:
                self.uiBinFile.edtBtType.setText(file_path)
                Local_Data_Util.fwSharedData["btPath"] = file_path
            else:
                self.showWarningInfo(Language_Util.getValue("dlg_bin_name_error"))

    def on_voice_select_event(self):
        file_path, _ = QFileDialog.getOpenFileName(self.mParentWindow,
                                                   Language_Util.getValue("dlg_fw_select_file"),
                                                   "", "BIN Files (*.bin)")
        if file_path:
            fileName = os.path.basename(file_path)
            matchObj = re.match(Config_Data.BIN_FILE_REGEX_VOICE, fileName)
            if matchObj:
                self.uiBinFile.edtVoiceType.setText(file_path)
                Local_Data_Util.fwSharedData["voicePath"] = file_path
            else:
                self.showWarningInfo(Language_Util.getValue("dlg_bin_name_error"))

    def on_demo_select_event(self):
        file_path, _ = QFileDialog.getOpenFileName(self.mParentWindow,
                                                   Language_Util.getValue("dlg_fw_select_file"),
                                                   "", "BIN Files (*.bin)")
        if file_path:
            fileName = os.path.basename(file_path)
            matchObj = re.match(Config_Data.BIN_FILE_REGEX_DEMO, fileName)
            if matchObj:
                self.uiBinFile.edtDemoType.setText(file_path)
                Local_Data_Util.fwSharedData["demoPath"] = file_path
            else:
                self.showWarningInfo(Language_Util.getValue("dlg_bin_name_error"))

    def on_ok_event(self):
        # 分析是否需要保存数据
        boNeedSave = False
        if self.mSharedData["btPath"] != Local_Data_Util.fwSharedData["btPath"]:
            boNeedSave = True
            # 保存路径索引值
            Device_Filepath_Util.add_record(Device_Filepath_Util.getFileName(), Local_Data_Util.fwSharedData["btPath"])

        if self.mSharedData["voicePath"] != Local_Data_Util.fwSharedData["voicePath"]:
            boNeedSave = True
            # 保存路径索引值
            Device_Filepath_Util.add_record(Device_Filepath_Util.getFileName(), Local_Data_Util.fwSharedData["voicePath"])

        if self.mSharedData["demoPath"] != Local_Data_Util.fwSharedData["demoPath"]:
            boNeedSave = True
            # 保存路径索引值
            Device_Filepath_Util.add_record(Device_Filepath_Util.getFileName(), Local_Data_Util.fwSharedData["demoPath"])

        if boNeedSave:
            Local_Data_Util.saveData()
            # bin文件有更新,重新加载到缓存中
            Device_Filepath_Util.re_load_data()

        # 关闭当前界面
        self.close()

        # 调用回调事件,用于显示选择的文件路径
        if self.call_back_fun is not None:
            self.call_back_fun()

    def on_cancel_event(self):
        self.close()

    def setCallBack(self, call_back_fun):
        self.call_back_fun = call_back_fun

    def setParentWindow(self, parentWindow):
        self.mParentWindow = parentWindow

    def getView(self):
        return self.uiBinFile

    def showWarningInfo(self, info):
        tmpView = self.getView()
        tmpView.mWarning = QMessageBox(QMessageBox.Warning, Language_Util.getValue("dlg_com_warn"), info)
        tmpView.mWarning.show()