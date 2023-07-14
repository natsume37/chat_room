# coding:utf-8
# USER: 冷不丁
# @FILE_NAME: views
# @TIME: 2023/7/10 18:15
from db.models import User
from lib.common import *


async def register(conn, request_dic, *args, **kwargs):
    """
    注册接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    """
    LOGGER.debug('开始注册')
    user = request_dic.get('user')
    pwd = request_dic.get('pwd')
    if await User.select(user):
        request_dic = ResponseData.register_error_dic('用户 【{}】 已存在，请更换用户名'.format(user))
        await conn.send(request_dic)
        return

    user_obj = User(user, pwd)
    await user_obj.save()

    request_dic = ResponseData.register_success_dic("注册成功")
    await conn.send(request_dic)


async def login(conn, request_dic, *args, **kwargs):
    """
    登录接口接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    """
    LOGGER.debug('开始登录')
    user = request_dic.get('user')
    pwd = request_dic.get('pwd')
    user_obj = await User.select(user)

    if not user_obj or user_obj.pwd != pwd:
        request_dic = ResponseData.login_error_dic(user, '用户名或密码错误')
        await conn.send(request_dic)
        return
    # 同一账户只能登录一次
    if user in conn.online_users:
        request_dic = ResponseData.login_error_dic(user, '该用户已登录')
        await conn.send(request_dic)
        return

    # 保存当前的conn对象
    conn.online_users[user] = conn
    conn.name = user
    conn.token = generate_token(user)

    LOGGER.info('【{}】进入了聊天室'.format(user))

    request_dic = ResponseData.login_success_dic(user, "登录成功", conn.token)
    await conn.send(request_dic)

    # 广播信息
    response_dic = ResponseData.online_dic(user)
    await conn.put_q(response_dic)


async def reconnect(conn, request_dic, *args, **kwargs):
    """
    重连接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    """
    token = request_dic.get('token')
    user = request_dic.get('user')
    LOGGER.debug('{}开始重连'.format(user))
    if generate_token(user) != token:
        response_dic = ResponseData.reconnect_error_dic('token无效请重新登录')
        await conn.send(response_dic)
        return
    # 判断是否多次登录
    if user in conn.online_users:
        request_dic = ResponseData.reconnect_error_dic('已经在其他地方登录')
        await conn.send(request_dic)
        return
    # 保存当前的conn对象
    conn.online_users[user] = conn
    conn.name = user
    conn.token = token

    LOGGER.info('【{}】进入了聊天室'.format(user))

    request_dic = ResponseData.reconnect_success_dic()
    await conn.send(request_dic)

    # 广播信息
    response_dic = ResponseData.online_dic(user)
    await conn.put_q(response_dic)


async def chat(conn, request_dic, *args, **kwargs):
    """
    聊天接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    """
    token = request_dic.get('token')
    if token != conn.token:
        conn.close()
        return

    user = request_dic.get('user')
    msg = request_dic.get('msg')

    LOGGER.info('{}说：{}'.format(user, msg))

    response_dic = ResponseData.chat_dic(request_dic)
    LOGGER.debug(f'views-chat -response_dic {response_dic}')
    await conn.put_q(response_dic)


async def file(conn, request_dic, *args, **kwargs):
    """
    文件接口
    :param conn:
    :param request_dic:
    :param args:
    :param kwargs:
    :return:
    """
    token = request_dic.get('token')
    LOGGER.debug('开始file_函数')
    if token != conn.token:
        conn.close()
        return
    user = request_dic.get('user')
    file_name = request_dic.get('file_name')
    LOGGER.info('{}发了文件：{}'.format(user, file_name))

    response_dic = ResponseData.file_dic(request_dic)
    await conn.put_q(response_dic)
