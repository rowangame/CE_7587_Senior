from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyledItemDelegate


class CenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter  # 设置文本居中