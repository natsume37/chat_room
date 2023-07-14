# coding:utf-8
# USER: 冷不丁
# @FILE_NAME: urls
# @TIME: 2023/7/10 18:14
from core.views import *

route_mode = {
    'register': register,
    'login': login,
    'reconnect': reconnect,
    'chat': chat,
    'file': file
}
