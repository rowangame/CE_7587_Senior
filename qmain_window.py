# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QApplication


class QMaintoolsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mObserver = None

    def closeEvent(self, event):
        # # 分析是否有其它窗口打开，如果打开了，则全部关闭
        # for widget in QApplication.instance().allWidgets():
        #     if isinstance(widget, QMainWindow) and widget != self:
        #         widget.close()

        # 如果有观察者对象,由观察者对象处理逻辑
        if self.mObserver != None:
            if self.mObserver.onWindowCloseEvent != None:
                self.mObserver.onWindowCloseEvent(event)
                return

        # 接受事件回调
        event.accept()

    def setObserverObject(self, observer):
        self.mObserver = observer