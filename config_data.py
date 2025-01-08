# -*- coding: UTF-8 -*-
# @Time    : 2024/12/25 14:38
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : config_data.py
# @IDE     : PyCharm

class Config_Data:
    # 当前版本号
    TOOL_VERSION = "6.1"

    # 全局icon对象
    MAIN_ICON = None

    # 用户名
    ADMIN_NAME = "1"

    # 密码
    ADMIN_PSW = "1"

    # 选择固件文件时,需要用户登陆才能设置
    mAuthorized = False

    # 最多支持的线程升级数
    MAX_C_MODULE_COUNT = 5

    # 是否使用C模块进行升级(必须)
    USE_C_MODULE_PROCESS = True

    # 获取设备信息超时最大时间(超时升级失败 单位:秒)
    DEV_INFO_MAX_WAIT_TIME = 15

    # 升级最大的等待时间(超时升级失败 单位:秒)
    UPGRADE_MAX_WAIT_TIME = 300

    # BT -文件名格式 (如: XG_BT_FW_241224_1537A_DV2_DFU.bin)
    BIN_FILE_REGEX_BT = r"^XG_BT_FW_\d{6}_([A-Za-z0-9_]*)?_DFU\.bin$"

    # VOICE -文件名格式 (如: combined_prompt_V11_DFU.bin)
    BIN_FILE_REGEX_VOICE = r"^combined_prompt_V\d{2}_DFU\.bin$"

    # DEMO -文件名格式 (如: demoplay_sample_V03.bin)
    BIN_FILE_REGEX_DEMO = r"^demoplay_sample_V\d{2}\.bin$"