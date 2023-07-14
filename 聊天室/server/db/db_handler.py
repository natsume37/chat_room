# coding:utf-8
# user: 冷不丁
# @FILE_NAME: db_handler
# @time: 2023/7/7 08:38
"""
数据的增删改查
"""
import pickle

import aiofiles

from conf.setting import *
import os


async def save_data(obj):
    obj_path = os.path.join(USER_DIR, obj.name)
    async with aiofiles.open(obj_path, 'wb') as f:
        obj_bytes = pickle.dumps(obj)
        await f.write(obj_bytes)


async def select_data(name):
    obj_path = os.path.join(USER_DIR, name)
    if not os.path.exists(obj_path):
        return
    async with aiofiles.open(obj_path, 'rb')as f:
        obj_bytes = await f.read()
        obj = pickle.loads(obj_bytes)
        return obj

