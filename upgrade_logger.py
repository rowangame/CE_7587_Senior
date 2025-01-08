# -*- coding: UTF-8 -*-
# @Time    : 2024/12/27 15:19
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : upgrade_logger.py
# @IDE     : PyCharm

"""
警告:
    这里的日志打印信息,最多支持的数量必须小于多线程支持的数量,否则会严重异常
    参考: Data_Config.MAX_C_MODULE_COUNT
"""


class Upgrade_Logger:
    # 控制台打印信息 (需要将同一个升级单元对象打印的数据到一起,防止控制台数据混乱)
    mConsoleLst = [[], [], [], [], [], []]

    # 表格日志信息 (防止表格数据混乱)
    mTableLst = [[], [], [], [], [], []]

    @classmethod
    def clearAll(cls):
        for i in range(len(cls.mConsoleLst)):
            cls.mConsoleLst[i].clear()

        for i in range(len(cls.mTableLst)):
            cls.mTableLst[i].clear()

    @classmethod
    def clearConsoleLogByIndex(cls, index):
        cls.mConsoleLst[index].clear()

    @classmethod
    def clearTableLogByIndex(cls, index):
        cls.mTableLst[index].clear()

    @classmethod
    def addConsoleLog(cls, index: int, log: str):
        cls.mConsoleLst[index].append(log)

    @classmethod
    def addTableLog(cls, index: int, log: str):
        cls.mTableLst[index].append(log)

    @classmethod
    def getConsoleLogByIndex(cls, index: int):
        return cls.mConsoleLst[index]

    @classmethod
    def getTableLogByIndex(cls, index: int):
        return cls.mTableLst[index]