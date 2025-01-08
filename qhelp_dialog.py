import os

from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog

from config_data import Config_Data
from dialog_help import Ui_diaHelp
from language_util import Language_Util


class QMyHelpDialog(QDialog):
    def __init__(self):
        super().__init__()

        uiHelp = Ui_diaHelp()
        uiHelp.setupUi(self)
        self.uiHelp = uiHelp

        self.setWindowTitle(Language_Util.getValue("dlg_help_title"))
        self.setFixedSize(549, 311)

        uiHelp.lbl_sp_1.setText(Language_Util.getValue("dlg_help_sp1"))
        uiHelp.lbl_sp_2.setText(Language_Util.getValue("dlg_help_sp2"))
        uiHelp.lbl_sp_3.setText(Language_Util.getValue("dlg_help_sp3"))
        uiHelp.lbl_sp_4.setText(Language_Util.getValue("dlg_help_sp4"))

        uiHelp.lbl_tip_1.setText(Language_Util.getValue("dlg_help_note1"))
        strType = Language_Util.getValue('dlg_help_note_type')
        strFile = Language_Util.getValue('dlg_help_note_file')
        uiHelp.lbl_tip_2.setText(f"1.BT {strType}->{strFile}(XG_BT_FW_*_DFU.bin)")
        uiHelp.lbl_tip_3.setText(f"2.Voice {strType}->{strFile}(combined_*_DFU.bin)")
        uiHelp.lbl_tip_4.setText(f"3.Demo {strType}->{strFile}(demoplay_*.bin)")
        uiHelp.btnOK.setText(Language_Util.getValue("dlg_fw_confirm"))

        iconPath = os.getcwd() + "\\resources\\ico-help.png"
        # 将图片路径设置为QLabel的背景
        uiHelp.lblLogo.setPixmap(QPixmap(iconPath))
        # 确保图片适应标签大小
        uiHelp.lblLogo.setScaledContents(True)

        # 设置icon
        self.setWindowIcon(Config_Data.MAIN_ICON)

        uiHelp.btnOK.clicked.connect(self.on_ok_event)

    def on_ok_event(self):
        self.close()
