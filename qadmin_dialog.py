
from PyQt5.QtWidgets import QLineEdit, QDialog, QMessageBox
from config_data import Config_Data
from dialog_admin import Ui_dia_admin
from language_util import Language_Util


class QAdmin_Dialog(QDialog):
    def __init__(self):
        super().__init__()

        uiCom = Ui_dia_admin()
        uiCom.setupUi(self)
        self.uiCom = uiCom
        self.setWindowIcon(Config_Data.MAIN_ICON)

        self.setWindowTitle(Language_Util.getValue("admin_title"))
        # 设置对话框大小不可调节
        self.setFixedSize(270, 131)

        uiCom.lblName.setText(Language_Util.getValue("admin_name"))
        uiCom.lblPsw.setText(Language_Util.getValue("admin_psw"))
        uiCom.btnOK.setText(Language_Util.getValue("admin_ok"))

        self.uiCom.edtPsw.setEchoMode(QLineEdit.Password)
        uiCom.btnOK.clicked.connect(self.on_ok_event)

        # 授权成功后,是否需要回调事件
        self.call_back_fun = None

    def on_ok_event(self):
        # 当点击确认按钮时，记录输入的用户名和密码
        name = self.uiCom.edtName.text()
        psw = self.uiCom.edtPsw.text()
        # print(f"name:{name} psw:{psw}")
        if (Config_Data.ADMIN_NAME != name) or (Config_Data.ADMIN_PSW != psw):
            info = Language_Util.getValue("admin_login_error")
            # 这里需要将对话框赋值给当前对象,要不显示后马上消失(？对象被释放掉了)
            self.mWarning = QMessageBox(QMessageBox.Warning, Language_Util.getValue("dlg_title_warn"), info)
            self.mWarning.setWindowIcon(Config_Data.MAIN_ICON)
            self.mWarning.show()
            Config_Data.mAuthorized = False
        else:
            Config_Data.mAuthorized = True
            self.close()
            if self.call_back_fun is not None:
                self.call_back_fun()

    def setCallBack(self, call_back_fun):
        self.call_back_fun = call_back_fun