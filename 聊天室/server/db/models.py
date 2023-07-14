# coding:utf-8
# user: 冷不丁
# @FILE_NAME: models
# @time: 2023/7/7 08:36
"""
模型层
"""
from db import db_handler


class User:
    def __init__(self, name, pwd):
        self.name = name
        self.pwd = pwd

    async def save(self):
        await db_handler.save_data(self)

    @staticmethod
    async def select(name):
        return await db_handler.select_data(name)