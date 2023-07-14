# coding:utf-8
# user: 冷不丁
# @FILE_NAME: start
# @time: 2023/7/7 11:30
"""
入口文件
"""
from core import client
# 猴子补丁（给UI的py文件增加功能）

# 错误示范
# from PyQt6.QtWidgets import QTextEdit
#
# QTextEdit = client.MyTextEdit

# 正确示范
from PyQt6 import QtWidgets

QtWidgets.QTextEdit = client.MyTextEdit

if __name__ == '__main__':
    client.run()
