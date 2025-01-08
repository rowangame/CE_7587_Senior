import os

# 打包命令(将依赖项打包到目录下)
CMD_STRT_TAG = "pyinstaller -D -w -i "
HIDDEN_IMPORT = "--hidden-import %s "
ICON_NAME = "logo.ico "
MAIN_PY = "upgrade_main.py"

if __name__ == "__main__":
    cwd = os.getcwd()

    # 编译命令
    cmd_info = CMD_STRT_TAG
    # icon命令
    cmd_info += cwd + "\\" + ICON_NAME
    # 主目录
    lstFiles = os.listdir(cwd)
    for tmpF in lstFiles:
        if tmpF == MAIN_PY:
            cmd_info += MAIN_PY + " "
            break

    # 隐藏文件(除去本身)
    selfFile = os.path.basename(__file__)
    for tmpF in lstFiles:
        if tmpF.endswith(".py"):
            if tmpF == selfFile:
                continue
            if tmpF != MAIN_PY:
                cmd_info += HIDDEN_IMPORT % tmpF

    print(cmd_info)