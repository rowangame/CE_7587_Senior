# -*- coding: UTF-8 -*-
# @Time    : 2025/1/4 9:14
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : device_csv_util.py
# @IDE     : PyCharm

import csv
import os.path
import time


class Device_Csv_Util:
    FILENAME_PREFIX = "devices"

    FILENAME = FILENAME_PREFIX + ".csv"

    # 定义字段名
    FIELDNAMES = ["Mac", "Version", "BT", "Voice", "Demo", "OpTime"]

    # 文件记录大于指定行数后,需要开始新的文件记录(提高写入效率)
    MAX_RECORDS = 1000

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
    def add_or_update_record(cls, csvFile: str, mac: str, version: str, bt: str, voice: str, demo: str):
        """
        添加或更新记录
        :param csvFile:
            csvFile 文件路径
        :param mac:
            设备Mac地址
        :param version:
            设备版本号
        :param bt:
            BinPathId#[Pass,Fail,Ignore,None]  bt类型文件路径Id#状态(成功,失败,忽略,无操作)
        :param voice:
            BinPathId#[Pass,Fail,Ignore,None]  voice类型文件路径Id#状态(成功,失败,忽略,无操作)
        :param demo:
            BinPathId#[Pass,Fail,Ignore,None]  demo类型文件路径Id#状态(成功,失败,忽略,无操作)
        :return:
            record: {"Mac", "Version", "BT", "Voice", "Demo", "OpTime"}
        """
        updated = False
        records = []
        rltRecord = None
        # 这里根据需要添加了最后的操作时间
        strOpTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

        # 如果查询设备信息为空,则不保存记录数据,只返回默认数据(兼容UI显示)
        boNeedSave = (len(mac) > 0) and (len(version) > 0)
        if not boNeedSave:
            new_record = {
                "Mac": "None",
                "Version": "None#None#None",
                "BT": bt,
                "Voice": voice,
                "Demo": demo,
                "OpTime": strOpTime
            }
            return new_record

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Mac"] == mac:
                    # 更新现有记录
                    row["Version"] = version
                    row["BT"] = bt
                    row["Voice"] = voice
                    row["Demo"] = demo
                    row["OpTime"] = strOpTime
                    updated = True
                    rltRecord = row
                records.append(row)

        # 如果没有找到Mac，添加新记录
        if not updated:
            new_record = {
                "Mac": mac,
                "Version": version,
                "BT": bt,
                "Voice": voice,
                "Demo": demo,
                "OpTime": strOpTime
            }
            rltRecord = new_record

            # 如果记录数大于指定文件,则需要将当前文件数据复制到新文件中,并重新创建新的文件记录
            tmpRecordCnt = len(records)
            if tmpRecordCnt + 1 > cls.MAX_RECORDS:
                tmpParentPath = os.path.dirname(csvFile)
                tmpFiles = os.listdir(tmpParentPath)
                tmpCsvFileCnt = 0
                for tmpFileName in tmpFiles:
                    if tmpFileName.startswith(cls.FILENAME_PREFIX):
                        tmpCsvFileCnt += 1
                tmpBakCsvFile = tmpParentPath + "/" + "%s-%d.csv" % (cls.FILENAME_PREFIX, tmpCsvFileCnt)
                with open(tmpBakCsvFile, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=cls.FIELDNAMES)
                    writer.writeheader()  # 写入表头
                    writer.writerows(records)  # 写入所有记录
                # 清除已保存的所有记录
                records.clear()

            records.append(new_record)

        # 将数据写回文件
        with open(csvFile, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=cls.FIELDNAMES)
            writer.writeheader()  # 写入表头
            writer.writerows(records)  # 写入所有记录

        return rltRecord

    @classmethod
    def find_record_by_mac(cls, csvFile: str, mac: str):
        """
        查询记录是否存在
        :param csvFile:
            csvFile 文件路径
        :param mac:
            设备Mac地址
        :return:
            csv文件对应的mac行记录
        """
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Mac"] == mac:
                    return row  # 返回找到的记录
        # 如果没有找到，返回None
        return None

    @classmethod
    def delete_record_by_mac(cls, csvFile: str, mac: str):
        """
        删除记录
        :param csvFile:
            csvFile 文件路径
        :param mac:
            设备Mac地址
        :return:
        """
        records = []

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Mac"] != mac:
                    records.append(row)  # 只保留不匹配的记录

        # 将数据写回文件
        with open(csvFile, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=cls.FIELDNAMES)
            writer.writeheader()  # 写入表头
            writer.writerows(records)  # 写入所有保留的记录

    @classmethod
    def get_all_records(cls, csvFile: str):
        """
        得到文件所有记录
        :param csvFile:
            csvFile文件名
        :return:
            记录列表
        """
        records = []

        # 读取CSV文件内容
        with open(csvFile, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                records.append(row)

        return records