# -*- coding: UTF-8 -*-
# @Time    : 2025/1/4 9:31
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : device_filepath_util.py
# @IDE     : PyCharm

import csv
import os.path


class Device_Filepath_Util:
    FILENAME_PREFIX = "filepath"

    FILENAME = FILENAME_PREFIX + ".csv"

    # 定义字段名
    # "Index" 文件路径对应的ID号(0:无效 1~N有效值 优化保存数据时,减少文件路径数据冗长的问题)
    # "Filepath" bt,voice,demo对应的文件路径
    FIELDNAMES = ["Index", "Filepath"]

    # 总记录数(缓存数据,用于加快数据访问)
    mRecords = []

    @classmethod
    def getFilePath(cls):
        """
        根据版本号,得到目录
        :return:
            目录路径(如果目录不存在,则创建目录)
        """
        curPath = os.getcwd()
        tmpPath = curPath + f"\\data\\records\\"
        if not os.path.exists(tmpPath):
            os.makedirs(tmpPath)
        return tmpPath

    @classmethod
    def getFileName(cls):
        """
        得到csv文件路径
        :return:
            csv文件路径(如果文件不存在,则创建文件,并写入表头)
        """
        parentPath = cls.getFilePath()
        tmpCsvFile = parentPath + cls.FILENAME

        # 初始化文件, 写入表头（如果文件不存在）
        if not os.path.exists(tmpCsvFile):
            with open(tmpCsvFile, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=cls.FIELDNAMES)
                writer.writeheader()
        return tmpCsvFile

    @classmethod
    def add_record(cls, csvFile: str, binFilePath: str):
        """
        添加或更新记录
        :param csvFile:
             csvFile 文件路径
        :param binFilePath:
             bin类型文件路径
        :return:
            record: {"Index", "Filepath"}
        """
        records = []

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                records.append(row)

        # 如果存在,直接返回记录
        for row in records:
            if row["Filepath"] == binFilePath:
                return row

        # 索引值从1开始 (0:表示无效路径)
        indexValue = len(records) + 1
        new_record = {"Index": indexValue, "Filepath": binFilePath}
        records.append(new_record)

        # 将数据写回文件
        with open(csvFile, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=cls.FIELDNAMES)
            writer.writeheader()  # 写入表头
            writer.writerows(records)  # 写入所有记录

        return new_record

    @classmethod
    def find_record_by_path(cls, binFilePath: str):
        """
        查询记录是否存在
        :param binFilePath:
            binFilePath文件路径
        :return:
            csv文件对应的binFilePath行记录
        """
        for row in cls.mRecords:
            if row["Filepath"] == binFilePath:
                return row  # 返回找到的记录
        # 如果没有找到，返回None
        return None

    @classmethod
    def find_record_by_index(cls, index: int):
        """
        查询记录是否存在
        :param index:
            index bin文件路径索引值
        :return:
            csv文件对应的binFilePath行记录
        """
        if index > 0:
            for row in cls.mRecords:
                if int(row["Index"]) == index:
                    return row  # 返回找到的记录
        # 如果没有找到，返回None
        return None

    @classmethod
    def find_filepath_by_index(cls, index: int):
        tmpRecord = cls.find_record_by_index(index)
        if tmpRecord is not None:
            return tmpRecord["Filepath"]
        else:
            return "None"

    @classmethod
    def find_index_by_filepath(cls, binFilePath: str):
        tmpRecord = cls.find_record_by_path(binFilePath)
        if tmpRecord is not None:
            return tmpRecord["Index"]
        return 0

    @classmethod
    def get_all_records(cls, csvFile: str):
        """
        得到文件所有记录
        :param csvFile:
            csvFile文件名
        :return:
            记录列表
        """
        cls.mRecords.clear()

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cls.mRecords.append(row)

        return cls.mRecords

    @classmethod
    def re_load_data(cls):
        csvFile = cls.getFileName()
        cls.mRecords.clear()

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cls.mRecords.append(row)