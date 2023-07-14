# coding:utf-8
# user: 冷不丁
# @FILE_NAME: tests_start_server
# @time: 2023/7/7 08:40
import asyncio


async def client_handel(reader, writer):
    while True:
        try:
            data = await reader.read(1024)
            if not data:
                break
            writer.write(data.upper())
            # 缓冲区数据立即被发送
            await writer.drain()
        except ConnectionResetError:
            break
    writer.close()


async def run_server():
    server = await asyncio.start_server(client_handel, "localhost", 8080)
    # 异步上下文管理器（优雅的有异常处理方法）
    async with server:
        await server.serve_forever()


asyncio.run(run_server())


