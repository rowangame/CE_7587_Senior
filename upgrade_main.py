import os
import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

from config_data import Config_Data
from language_util import Language_Util
from local_data_util import Local_Data_Util
from qmain_window import QMaintoolsWindow
from view_main_manager import View_Main_Manager


def showUpgradeView():
    app = QApplication(sys.argv)
    myMainWindow = QMaintoolsWindow()
    myMainWindow.setObserverObject(View_Main_Manager)

    # 加载配置文件
    Local_Data_Util.loadData()
    Language_Util.loadConfigFile()

    # 初始化主界面
    View_Main_Manager.getView().setupUi(myMainWindow)
    # 设置主窗口属性
    View_Main_Manager.setMainWindow(myMainWindow)
    # 初始化事件
    View_Main_Manager.initEvents()

    # 禁止窗口最大化
    # myMainWindow.setFixedWidth(myMainWindow.width())
    # myMainWindow.setFixedHeight(myMainWindow.height())

    # # 居中显示(这里双屏幕的电脑显示会出问题,所以不做居中显示)
    # desktop = QApplication.desktop()
    # tmpRect = myMainWindow.geometry()
    # tmpX = (desktop.width() - tmpRect.width()) // 2 - 200
    # tmpY = (desktop.height() - tmpRect.height()) // 2
    # myMainWindow.move(int(tmpX), int(tmpY))

    # 设置最小宽度和最小高度
    myMainWindow.setMinimumWidth(500)  # 设置最小宽度
    myMainWindow.setMinimumHeight(400)  # 设置最小高度

    # 设置标题
    myMainWindow.setWindowTitle(f"CE_7587&7588-{Language_Util.getValue('wnd_title')}-V{Config_Data.TOOL_VERSION}")

    # 设置窗口图标(此方法占内存多,但图标显示效果较好,适用于较小的图片)
    ico_path = os.getcwd() + "\\resources\\main_logo.png"
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(ico_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    Config_Data.MAIN_ICON = icon
    myMainWindow.setWindowIcon(Config_Data.MAIN_ICON)

    myMainWindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    showUpgradeView()
