# coding:utf-8
# user: 冷不丁
# @FILE_NAME: common
# @time: 2023/7/7 11:29
"""
公共方法
"""
import hashlib
import time
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox

from conf.setting import *


# 哈希加密
def hash_pwd(pwd):
    hash_obj = hashlib.sha256()
    hash_obj.update('冷不'.encode('utf-8'))
    hash_obj.update(pwd.encode('utf-8'))
    hash_obj.update('丁'.encode('utf-8'))
    return hash_obj.hexdigest()


def get_time():
    # 去除微秒后的结果
    return datetime.now().replace(microsecond=0)


def get_file_info(file_path):
    file_name = os.path.basename(file_path)
    hash_obj = hashlib.md5()
    with open(file_path, 'rb') as f:
        f.seek(0, 2)
        file_size = f.tell()
        one_tenth = file_size // 10
        for i in range(10):
            f.seek(i * one_tenth, 0)
            res = f.read(100)
            hash_obj.update(res)
        return file_name, file_size, hash_obj.hexdigest()


# 重连处理装饰器
def reconnect(fn):
    def wrapper(*args, **kwargs):
        self = args[0]
        try:
            res = fn(*args, **kwargs)
        except Exception as e:
            LOGGER.debug('连接断开、正在重连{}'.format(e))
            self.tip_label.setText('连接断开，正在重连....')
            # 根据文字大小自动调整标签大小
            self.tip_label.setFixedSize(self.tip_label.size())
            self.tip_label.adjustSize()
            self.tip_label.show()
            # 重连
            self.client.close()
            res = self.client.connect()
            self.tip_label.close()
            if res:
                return
            QMessageBox.warning(self, '提示', '连接服务器失败， 即将关闭程序')
            exit()
        return res

    return wrapper


def reconnect_t(fn):
    def wrapper(*args, **kwargs):
        self = args[0]
        try:
            res = fn(*args, **kwargs)
        except Exception as e:
            LOGGER.error(f'连接断开、正在重连{e}  这')
            # 信号
            self.reconnected.emit('show_tip')

            # 重连

            self.client.close()
            res = self.client.connect()

            # 信号
            self.reconnected.emit('close_tip')

            if res:
                return
            # 发信号
            self.reconnected.emit('over')
            import time
            time.sleep(0.1)
            self.terminate()
        return res

    return wrapper


def byte_to_human(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    for unit in units:
        if size < 1024 or unit == 'PB':
            return '{:.2f} {}'.format(size, unit)
        size /= 1024


class RequestData:
    @staticmethod
    def register_dic(user, pwd, *args, **kwargs):
        """
        组织注册字典
        :param user:
        :param pwd:
        :param args:
        :param kwargs:
        :return:
        """
        # 注册请求格式
        request_dic = {
            'mode': RESPONDSt_REGISTER,
            'user': user,
            'pwd': hash_pwd(pwd)
        }
        return request_dic

    @staticmethod
    def login_dic(user, pwd, *args, **kwargs):
        """
        登录请求字典
        :param user:
        :param pwd:
        :param args:
        :param kwargs:
        :return:
        """
        request_dic = {
            'mode': RESPONDSt_LOGIN,
            'user': user,
            'pwd': hash_pwd(pwd)
        }
        return request_dic

    @staticmethod
    def chat_dic(user, msg, token, *args, **kwargs):
        """
        聊天请求字典
        :param user:
        :param msg:
        :param token:
        :param args:
        :param kwargs:
        :return:
        """
        request_dic = {
            'mode': RESPONDSt_CHAT,
            'user': user,
            'msg': msg,
            'time': get_time(),
            'token': token
        }
        return request_dic

    @staticmethod
    def file_dic(user, file_path, token, *args, **kwargs):
        """
        组织文件字典
        :param user:
        :param file_path:
        :param token:
        :param args:
        :param kwargs:
        :return:
        """
        file_name, file_size, md5 = get_file_info(file_path)
        request_dic = {
            'mode': RESPONDSt_FILE,
            'user': user,
            'file_name': file_name,
            'file_size': file_size,
            'md5': md5,
            'time': get_time(),
            'token': token,
            'file_path': file_path
        }
        return request_dic

    @staticmethod
    def reconnect_dic(user, token, *args, **kwargs):
        """
        重连请求字典
        :param user:
        :param token:
        :param args:
        :param kwargs:
        :return:
        """
        request_dic = {
            'mode': RESPONDSt_RECONNECT,
            'user': user,
            'token': token
        }
        return request_dic
