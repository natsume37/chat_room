# coding:utf-8
# user: 冷不丁
# @FILE_NAME: setting
# @time: 2023/7/7 11:28
"""
配置文件
"""
import os
import logging.config

# 服务器地址配置
HOST = 'localhost'
PORT = 9000

# 协议配置
RESPONDSt_REGISTER = 'register'
RESPONDSt_LOGIN = 'login'
RESPONDSt_CHAT = 'chat'
RESPONDSt_FILE = 'file'
RESPONDSt_RECONNECT = 'reconnect'
RESPONSE_ONLINE = 'online'
RESPONSE_OFFLINE = 'offline'
PROTOCOL_LENGTH = 8

# 颜色配置
USER_COLOR = '#ee7959'
OTHER_USER_COLOR = 'red'

MY_MSG_COLOR = '#222f3e'
OTHER_BCK_COLOR = '#ffffff'
MY_BCK_COLOR = '#95ec69'

FONT_NAME_SIZE = 10

# 图片配置
IMGS_TYPES = ['jpg', 'jpeg', 'png', 'jif', 'bmp']

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # 项目根目录
INFO_LOG_DIR = os.path.join(BASE_DIR, "log", 'info.log')
ERROR_LOG_DIR = os.path.join(BASE_DIR, "log", 'error.log')
IMG_DIR = os.path.join(BASE_DIR, 'imgs')
FILE_DIR = os.path.join(BASE_DIR, 'datas')

LEVEL = 'DEBUG'

LOGGING_DIC = {
    'version': 1.0,
    'disable_existing_loggers': False,
    # 日志格式
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(threadName)s:%(thread)d [%(name)s] %(levelname)s [%(pathname)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(asctime)s [%(name)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'test': {
            'format': '%(asctime)s %(message)s',
        },
    },
    'filters': {},
    # 日志处理器
    'handlers': {
        'console_debug_handler': {
            'level': LEVEL,  # 日志处理的级别限制
            'class': 'logging.StreamHandler',  # 输出到终端
            'formatter': 'simple'  # 日志格式
        },
        'file_info_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件,日志轮转
            'filename': INFO_LOG_DIR,
            'maxBytes': 1024 * 1024 * 10,  # 日志大小 10M
            'backupCount': 10,  # 日志文件保存数量限制
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
        'file_error_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件,日志轮转
            'filename': ERROR_LOG_DIR,
            'maxBytes': 1024 * 1024 * 10,  # 日志大小 10M
            'backupCount': 10,  # 日志文件保存数量限制
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
    },
    # 日志记录器
    'loggers': {
        '': {  # 导入时logging.getLogger时使用的app_name
            'handlers': ['console_debug_handler', 'file_info_handler'],  # 日志分配到哪个handlers中
            'level': 'DEBUG',  # 日志记录的级别限制
            'propagate': False,  # 默认为True，向上（更高级别的logger）传递，设置为False即可，否则会一份日志向上层层传递
        },
        'error_logger': {  # 导入时logging.getLogger时使用的app_name
            'handlers': ['file_error_handler', 'console_debug_handler'],  # 日志分配到哪个handlers中
            'level': 'ERROR',  # 日志记录的级别限制
            'propagate': False,  # 默认为True，向上（更高级别的logger）传递，设置为False即可，否则会一份日志向上层层传递
        },
    }
}
# 注：进行日志轮转的日志文件，不能和其他handler共用，不然会导致文件被占用无法更名而报错！

logging.config.dictConfig(LOGGING_DIC)
LOGGER = logging.getLogger('client')
ERROR_LOG_DIR = logging.getLogger('error_logger')
