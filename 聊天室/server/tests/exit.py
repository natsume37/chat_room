# coding:utf-8
# user: 冷不丁
# @FILE_NAME: exit
# @time: 2023/7/7 09:22
import traceback

from conf.setting import *


class Test:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print(exc_type.__name__)
        # print(exc_val)
        # print(exc_tb.tb_lineno)
        #
        # traceback.print_tb(exc_tb)
        if exc_type is not None:
            ERROR_LOG_DIR.error('{}: {} {}'.format(
                exc_type.__name__, exc_val, exc_tb.tb_frame
            ))
        # return True


with Test() as t:
    t.xxxxx
print('aaa')