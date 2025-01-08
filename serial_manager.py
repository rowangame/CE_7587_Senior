# -*- coding: UTF-8 -*-
# @Time    : 2024/12/2514:52
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : serial_manager.py
# @IDE     : PyCharm

import time

import serial

"""
串口管理类-支持对不同发指令
"""


class Serial_Manager:
    BAUD_RATE = 921600
    DATA_BIT = 8
    PARITY = None
    STOP_BIT = 1
    FLOW_CONTROL = None

    TIME_OUT = 0.05
    OVER_TIME = 3000
    WAIT_RETRY_TIME = 0.1

    serial_container = {}

    @classmethod
    def openSerial(cls, com: str):
        try:
            # 警告: 使用 cls.serial_container[com]方式访问,会有异常
            # 需要用 get方式访问
            if cls.serial_container.get(com) is not None:
                cls.closeSerial(com)

            serial_obj = serial.Serial()
            serial_obj.port = com
            serial_obj.baudrate = cls.BAUD_RATE
            serial_obj.stopbits = serial.STOPBITS_ONE
            serial_obj.bytesize = serial.EIGHTBITS
            serial_obj.parity = serial.PARITY_NONE
            serial_obj.timeout = cls.BAUD_RATE
            serial_obj.open()

            cls.serial_container[com] = serial_obj

            return True
        except Exception as e:
            print(f"Error to open serial:{com},msg={repr(e)}")
            return False

    @classmethod
    def closeSerial(cls, com):
        if cls.serial_container.get(com) is not None:
            try:
                cls.serial_container.get(com).close()
            except Exception as e:
                print(f"Error to close serial:{com}, msg={repr(e)}")
            cls.serial_container[com] = None

    @classmethod
    def sendATCommand(cls, com: str, command: str):
        serial_obj = cls.serial_container.get(com)
        if serial_obj is None:
            return False, []

        try:
            tmpBuf = command.encode("utf-8")
            # 这里不打印提示信息(多线程会导致打印的提示信息混乱)
            # print(f"[{com}] send->", tmpBuf)
            serial_obj.write(tmpBuf)
            serial_obj.flush()

            resBuffer = []
            last_ms = time.time() * 1000
            while True:
                count = serial_obj.inWaiting()
                if count > 0:
                    tmpRdBuf = serial_obj.read(count)
                    tmpResInfo = tmpRdBuf.decode("utf-8")
                    # print(f"[{com}] rec->", tmpResInfo)
                    resBuffer.append(tmpResInfo)
                    break
                dtime = time.time() * 1000 - last_ms
                if dtime > cls.OVER_TIME:
                    print(f"[{com}] Reading data timeout")
                    break
                time.sleep(cls.WAIT_RETRY_TIME)
            return len(resBuffer) > 0, resBuffer
        except Exception as e:
            print(f"[{com}] sendATCommand error:",repr(e))
            return False, []

