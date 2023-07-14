# coding:utf-8
# user: 冷不丁
# @FILE_NAME: server
# @time: 2023/7/7 08:35
"""
核心逻辑
"""

import asyncio

from lib.common import *
from core.urls import route_mode


class Chatserver:
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        asyncio.run(asyncio.wait([self.run_server(), MyConn.send_all()]))

    async def client_handel(self, reader, writer):
        async with MyConn(reader, writer) as conn:
            while True:
                request_dic = await conn.recv()
                fn = route_mode.get(request_dic.get('mode'))
                await fn(conn, request_dic)

    async def run_server(self):
        server = await asyncio.start_server(self.client_handel, self.host, self.port)
        # 异步上下文管理器（优雅的有异常处理方法）
        async with server:
            LOGGER.debug('服务端启动成功 {}'.format((self.host, self.port)))
            await server.serve_forever()


def run():
    Chatserver(HOST, PORT)
