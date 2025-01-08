# -*- coding: UTF-8 -*-
# @Time    : 2024/12/25 15:53
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : upgrade_manager.py
# @IDE     : PyCharm
from upgrade_cell import Upgrade_Cell


class Upgrade_Manager:
    mCells = []

    @classmethod
    def addUpgradeCell(cls, upCell: Upgrade_Cell):
        cls.mCells.append(upCell)
        return True

    @classmethod
    def getUpgradeCellByCom(cls, comNum: str):
        for tmpCell in cls.mCells:
            if tmpCell.mComNum == comNum:
                return tmpCell
        return None

    @classmethod
    def getUpgradeCellByIndex(cls, index: int):
        for tmpCell in cls.mCells:
            if tmpCell.mIndex == index:
                return tmpCell
        return None

    @classmethod
    def getUpgradeIndexByCom(cls, comNum: str):
        for tmpCell in cls.mCells:
            if tmpCell.mComNum == comNum:
                return tmpCell.mIndex
        return 0

    @classmethod
    def getUpgradeComListInfo(cls):
        lstCom = []
        for tmpCell in cls.mCells:
            lstCom.append(tmpCell.mComNum)
        if len(lstCom) > 0:
            tmpStrCom = ''
            tmpSize = len(lstCom)
            for i in range(tmpSize):
                if i < tmpSize - 1:
                    tmpStrCom += lstCom[i] + ","
                else:
                    tmpStrCom += lstCom[i]
            return f"[{tmpStrCom}]"
        return ""

    @classmethod
    def clearAll(cls):
        for tmpCell in cls.mCells:
            tmpCell.clear()
        cls.mCells.clear()

    @classmethod
    def isUpgradeProcessing(cls):
        """
        :return:
            如果有一个升级单元在升级,则认为是升级状态,就不能关闭当前UI主界面
        """
        for tmpCell in cls.mCells:
            if tmpCell.mUpgradeProcessing:
                return True
        return False

    @classmethod
    def getUpgradeCount(cls):
        """
        :return:
            0: 表示当前选择的对象为空,则不能升级
        """
        count = 0
        for tmpCell in cls.mCells:
            if (tmpCell is not None) and (len(tmpCell.mComNum) > 0):
                count += 1
        return count
