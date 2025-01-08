# -*- coding: UTF-8 -*-
# @Time    : 2024/10/2310:36
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : language_util.py
# @IDE     : PyCharm
import os

from local_data_util import Local_Data_Util


class Language_Util:
    boLoaded: bool = False

    CODE_CN = "CN"
    CODE_EN = "EN"
    CODE_KR = "KR"

    lang_cn = []
    lang_en = []
    lang_kr = []

    @classmethod
    def loadConfigFile(cls):
        if cls.boLoaded:
            return
        try:
            pPath = os.getcwd() + "\\language\\"
            fileName = pPath + "cn.txt"
            cls.loadLang(fileName, cls.lang_cn)

            fileName = pPath + "en.txt"
            cls.loadLang(fileName, cls.lang_en)

            fileName = pPath + "kr.txt"
            cls.loadLang(fileName, cls.lang_kr)

            cls.boLoaded = True
        except Exception as e:
            print(repr(e))

    @classmethod
    def loadLang(cls, fileName: str, lang_lst: list):
        # 打开文件
        with open(fileName, "r", encoding="utf-8") as file:
            # 按行读取文件内容
            lines = file.readlines()

        # 输出每一行
        for line in lines:
            tmpLine = line.strip()
            if len(tmpLine) > 0:
                tmpLines = tmpLine.split("=")
                lang_lst.append((tmpLines[0].strip(), tmpLines[1].strip()))

        return len(lang_lst) > 0

    @classmethod
    def getValue(cls, key: str):
        cur_language = cls.lang_cn
        if Local_Data_Util.fwSharedData["language"] == cls.CODE_EN:
            cur_language = cls.lang_en
        elif Local_Data_Util.fwSharedData["language"] == cls.CODE_KR:
            cur_language = cls.lang_kr
        for tmpKV in cur_language:
            if tmpKV[0] == key:
                return tmpKV[1]
        return ""

    @classmethod
    def getValueEx(cls, key: str, langCode: str):
        cur_language = cls.lang_cn
        if langCode == cls.CODE_EN:
            cur_language = cls.lang_en
        elif langCode== cls.CODE_KR:
            cur_language = cls.lang_kr
        for tmpKV in cur_language:
            if tmpKV[0] == key:
                return tmpKV[1]
        return ""