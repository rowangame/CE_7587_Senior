# -*- coding: UTF-8 -*-
# @Time    : 2024/12/25 15:20
# @Author  : xielunguo
# @Email   : xielunguo@cosonic.com
# @File    : upgrade_status.py
# @IDE     : PyCharm


class Upgrade_Status:
    # 烧入状态
    BS_FREE = 0
    # 开始请求同步状态
    BS_REQUEST_SYNC = 1
    # 数据传输中
    BS_DATA_TRANSFER = 2
    # 数据传输结束
    BS_DATA_TRANSFER_END = 3
    # 升级成功
    BS_UPGRADE_SUCCESS = 4
    # 升级出错
    BS_UPGRADE_ERROR = 5
    # 忽略升级
    BS_UPGRADE_IGNORE = 6

    # Q线程状态通知码
    SI_TAG_UPGRADE_START = "up_start"
    SI_TAG_INFO = "info"
    SI_TAG_ERROR = "error"
    SI_TAG_EXCEPT = "except"
    SI_TAG_PROGRESS = "progress"
    SI_TAG_SUCCESS = "success"
    SI_TAG_END = "end"
    SI_TAG_COPEN = "cpen"
    SI_TAG_CHSTATE = "chstate"
    SI_TAG_CMODULE_WAIT = "cm_wait"
    SI_TAG_AUTO_STATE = "at_state"
    SI_TAG_DEV_INFO_SECS = "dev_info_secs"
    SI_TAG_DEV_INFO_RLT = "dev_info"
    SI_TAG_CMP_VERSION = "cmp_version"
    SI_TAG_PROCESS_END = "prc_end"
    SI_TAG_QUERY_INFO = "query_info"
    SI_TAG_QUERY_END = "query_end"

    # 结果状态(等待设备重启,等待C模块启动,等待查询信息结果)
    # 无操作
    RLT_STATE_NONE = "None"
    # 忽略(版本相同或者升级文件为空等)
    RLT_STATE_IGNORE = "Ignore"
    # 升级失败(串口数据异常,文件读取异常,模块启动异常等)
    RLT_STATE_FAIL = "Fail"
    # 升级成功
    RLT_STATE_PASS = "Pass"
