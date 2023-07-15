# coding:utf-8
# user: 冷不丁
# @FILE_NAME: client
# @time: 2023/7/7 11:28
"""
核心逻辑
"""
import queue
import re
import socket
import time
import pickle
from datetime import timezone

from PyQt6.QtGui import QDropEvent, QImage
from PyQt6.QtWidgets import QApplication, QWidget, QTextEdit, QLabel, QListWidgetItem, QFileIconProvider
from PyQt6.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QTimer, QMargins, QFileInfo
from ui.login import Ui_Form as LoginUiMixin
from ui.chat import Ui_Form as ChatUiMixin
from lib.common import *


class MyTextEdit(QTextEdit):
    returnPressed = pyqtSignal()
    drop_event = pyqtSignal(list)

    # 重写回车信号、让它可以发送消息
    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key.Key_Return and not e.modifiers():  # 回车键 并且没有按 shift
            self.returnPressed.emit()
            return
        # 回调父类正常的操作函数
        super().keyPressEvent(e)

    # 重写拖拽事件
    def dropEvent(self, e: QDropEvent) -> None:
        # 拿用户的文件拖拽路径
        urls = []

        q_urls = e.mimeData().urls()
        for q_url in q_urls:
            url = q_url.toLocalFile()
            if os.path.isfile(url):
                urls.append(url)
        if not urls:
            return

        self.drop_event.emit(urls)


class MySocket:
    def __init__(self, host="localhost", port=9000):
        self.host = host
        self.port = port
        self.user = None
        self.token = None
        self.socket = None

    def send(self, data):
        return self.socket.send(data)

    def recv(self, recv_len):
        return self.socket.recv(recv_len)

    def send_data(self, dic):
        # 消息字典没有file_path,所以踹一下
        LOGGER.debug(f'dic  {dic}    send_data')
        try:
            file_path = dic.pop('file_path')
        except KeyError:
            pass
        dic_bytes = pickle.dumps(dic)
        len_bytes = len(dic_bytes).to_bytes(PROTOCOL_LENGTH, byteorder='big')
        self.send(len_bytes)
        self.send(dic_bytes)
        LOGGER.debug('发送字典完成')
        if dic.get('mode') != RESPONDSt_FILE:
            return
        # 发送文件
        print(f'文件路径  {file_path}')
        with open(file_path, 'rb') as f:
            LOGGER.debug("文件打开成功，开始发送文件")
            while True:
                temp = f.read(4096)
                if not temp:
                    break
                self.send(temp)
                LOGGER.debug('循环发送数据中')
            LOGGER.debug('文件发送完毕')

    def recv_data(self):
        len_bytes = self.recv(PROTOCOL_LENGTH)
        if not len_bytes:
            raise ConnectionResetError
        stream_len = int.from_bytes(len_bytes, byteorder='big')
        dic_bytes = bytes()
        while stream_len > 0:
            if stream_len < 4096:
                temp = self.recv(stream_len)
            else:
                temp = self.recv(4096)
            if not temp:
                raise ConnectionResetError
            dic_bytes += temp
            stream_len -= len(temp)
        response_dic = pickle.loads(dic_bytes)

        if response_dic.get('mode') != RESPONDSt_FILE:
            return response_dic
        # 接受文件类型
        return self.recv_file(response_dic)

    @staticmethod
    def rename(file_name):
        base, ext = os.path.split(file_name)
        pattern = re.compile(r'\((d+)\)$')
        res = pattern.search(base)
        if res:
            num = int(res.group(1)) + 1
            base = pattern.sub('({})'.format(num), base)

        else:
            base = '{}{}'.format(base, '(1)')
        return '{}{}'.format(base, ext)

    def recv_file(self, response_dic):
        file_size = response_dic.get('file_size')
        now_date = datetime.now().strftime('%Y-%m')
        file_dir = os.path.join(FILE_DIR, now_date)
        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)

        file_name = response_dic.get('file_name')
        file_path = os.path.join(file_dir, file_name)
        # 循环解决以下特殊情况
        # abc.txt  abc(1).txt abc.txt
        while True:
            if os.path.exists(file_path):
                file_name = self.rename(file_name)
                file_path = os.path.join(file_dir, file_name)
            else:
                response_dic['file'] = file_name
                break
        with open(file_path, 'wb') as f:
            while file_size > 0:
                if file_size < 4096:
                    temp = self.recv(file_size)
                else:
                    temp = self.recv(4096)
                if not temp:
                    raise ConnectionResetError
                f.write(temp)
                file_size -= len(temp)
            response_dic['file_path'] = file_path
        return response_dic

    def connect(self):
        for i in range(1, 4):
            try:
                self.socket = socket.socket()
                self.socket.connect((self.host, self.port))
                LOGGER.debug('连接服务器成功！')
                return True
            except Exception as e:
                LOGGER.error('连接服务器失败，开始第{}次重连 {}'.format(i, e))
                self.socket.close()
            time.sleep(2)

    def close(self):
        self.socket.close()

    def __enter__(self):
        if self.connect():
            return self
        else:
            exit()
            # return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()
        # pass


class LoginWindow(LoginUiMixin, QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setupUi(self)
        self.tip_label = QLabel()
        self.tip_label.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # 隐藏边框
        self.tip_label.setWindowModality(Qt.WindowModality.ApplicationModal)  # 模态窗口
        self.tip_label.setStyleSheet("background-color: gray")

        self.chat_window = None
        self.test()

    # 服务端发送数据
    @reconnect
    def get(self, dic):
        self.client.send_data(dic)  # 发送数据
        # 等待接收结果
        response_dic = self.client.recv_data()  # 收数据
        return response_dic

    def register(self):
        LOGGER.debug('注册')
        user = self.lineEdit_3.text().strip()
        pwd = self.lineEdit_4.text().strip()
        re_pwd = self.lineEdit_5.text().strip()
        if not user or not pwd or not re_pwd:
            QMessageBox.warning(self, "警告", '请填写完整！')
            return
        if pwd != re_pwd:
            QMessageBox.warning(self, "警告", '两次密码不一致！')
            return
        request_dic = RequestData.register_dic(user, pwd)
        response_dic = self.get(request_dic)
        if not response_dic:  # 重连成功
            return
        QMessageBox.about(self, '提示', response_dic.get('msg'))
        if response_dic.get('code') != 200:
            return
        # 注册成功后，清空注册的内容、跳转到登录页面自动填充账号焦点与密码
        # 设置空字符串
        self.lineEdit_3.setText('')
        self.lineEdit_4.setText('')
        self.lineEdit_5.setText('')
        self.lineEdit_2.setText('')
        self.open_login_page()
        self.lineEdit.setText(user)
        # 焦点聚焦与密码
        self.lineEdit_2.setFocus()

    def login(self):
        LOGGER.debug('登录')
        user = self.lineEdit.text().strip()
        pwd = self.lineEdit_2.text().strip()
        if not user or not pwd:
            QMessageBox.warning(self, "警告", '请填写完整！')
            return
        if not self.checkBox.isChecked():
            QMessageBox.warning(self, "警告", '请勾选服务协议！')
            return
        request_dic = RequestData.login_dic(user, pwd)
        response_dic = self.get(request_dic)
        if not response_dic:  # 重连成功
            return
        if response_dic.get('code') != 200:
            QMessageBox.about(self, '提示', response_dic.get('msg'))
            return

        self.client.user = user
        self.client.token = response_dic.get('token')

        notice = response_dic.get('notice')
        users = response_dic.get('users')

        # 打开聊天窗口、关闭登录窗口
        self.chat_window = ChatWindow(self, notice, users)
        self.chat_window.show()
        self.close()

    def open_register_page(self):
        LOGGER.debug('切换到注册页面')
        self.stackedWidget.setCurrentIndex(1)

    def open_login_page(self):
        LOGGER.debug('切换到登录页面')
        self.stackedWidget.setCurrentIndex(0)

    def protocol(self):
        LOGGER.debug('查看协议')
        QMessageBox.about(self, '服务协议', '此程序仅供冷不丁学习使用、有bug可以直接找我反映')

    def test(self):
        if LEVEL == 'DEBUG':
            self.lineEdit.setText('123')
            self.lineEdit_2.setText('123')
            self.checkBox.setChecked(True)


class ChatWindow(ChatUiMixin, QWidget):
    _translate = QCoreApplication.translate

    def __init__(self, login_window, notice, users):
        super().__init__()
        self.client = login_window.client
        self.login_window = login_window
        self.setupUi(self)
        # 设置重连标签
        self.tip_label = QLabel()
        self.tip_label.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # 隐藏标签
        self.tip_label.setWindowModality(Qt.WindowModality.ApplicationModal)  # 模拟窗口
        self.tip_label.setStyleSheet('background-color: #404042;')

        self.label.close()
        self.textBrowser.clear()
        self.textEdit.clear()
        self.textEdit_2.setText(notice)

        self.set_online_users(users)

        self.textEdit.drop_event.connect(self.confirm_send)
        self.textBrowser.anchorClicked.connect(self.open_url)

        self.request_q = queue.Queue()

        # 路由函数
        self.route_mode = {
            'reconnect': self.reconnect_res,
            'broadcast': self.broadcast_res,
            'chat': self.chat_res,
            'file': self.file_res
        }
        # 信号函数
        self.signal_route = {
            'show_tip': self.show_tip,
            'close_tip': self.tip_label.close,
            'over': self.over
        }

        self.last_time = datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)

        self.my_thead = MyThread(self.client)
        self.my_thead.reconnected.connect(self.t_signal)
        self.my_thead.received.connect(self.dic_handle)
        self.my_thead.start()

        self.send_thead = MyThread(self.client, self.request_q)
        self.send_thead.send_success.connect(self.send_success)
        self.send_thead.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close_broadcast)

        # 定义槽函数
        self.textEdit.returnPressed.connect(self.send_msg)

        # 设置聊天信息界面的边框距离
        self.textBrowser.setViewportMargins(QMargins(0, 0, 8, 0))

    def send_success(self, request_dic):
        LOGGER.debug(f'send_success  :{request_dic}  参数字典')
        self.append_time(request_dic.get('time'))
        if request_dic.get('mode') == RESPONDSt_FILE:
            self.show_file(request_dic, 'right')
            return
        self.textEdit.setText('')
        msg = request_dic.get('msg')
        # 获取光标对象
        self.cursor_end()
        self.textBrowser.insertHtml(
            f"""
                    <tr style="text-align:right">
                        <p>
                            <a class="one_a" style='color:{USER_COLOR};size:{FONT_NAME_SIZE}'>我</a>
                            <br />
                            <a class="two_a" style='color:{MY_MSG_COLOR};background-color:{MY_BCK_COLOR};border-radius: 5px;' >{msg}</a>
                        </p>
                    </tr>
                    """)
        self.cursor_end()

    @reconnect
    def put(self, request_dic):
        self.client.send_data(request_dic)
        return True

    @staticmethod
    def open_url(q_url):
        system_name = os.name
        # print(q_url.toLocalFile(), '文件路径')
        # 苹果用户
        if system_name == 'posix':
            os.system(r'open "{}"'.format(q_url.toLocalFile()))
            # os.system(r'open "{}{}{}"'.format(q_url.toLocalFile()[2:3], ':', q_url.toLocalFile()[3:]))
        # windows打开文件
        elif system_name == 'nt':
            os.system(r'start " " "{}{}{}'.format(q_url.toLocalFile()[2:3], ':', q_url.toLocalFile()[3:]))
            # print(r'start " " "{}{}{}'.format(q_url.toLocalFile()[2:3], ':', q_url.toLocalFile()[3:]))

    @staticmethod
    def get_icon(url):
        icon_path = os.path.join(IMG_DIR, '{}.png'.format(url.split('.')[-1]))
        if os.path.isfile(icon_path):
            return icon_path
        file_info = QFileInfo(url)
        file_icon = QFileIconProvider().icon(file_info)
        # 设置保存的图标大小
        file_icon.pixmap(50).save(icon_path)
        return icon_path

    def confirm_send(self, urls):
        files_info = '\n'
        for url in urls:
            file_name = os.path.basename(url)
            file_size = byte_to_human(os.path.getsize(url))
            files_info = '{}{} {}\n'.format(files_info, file_name, file_size)
        files_info = '{}\n是否发送？'.format(files_info)
        res = QMessageBox.question(self, '发送文件', files_info,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.No:
            return
        # 发送数据
        self.send_files(urls)

    def send_files(self, urls):
        for url in urls:
            request_dic = RequestData.file_dic(self.client.user, url, self.client.token)

            # 提交队列
            self.request_q.put(request_dic)
            LOGGER.debug('文件提交了到了文件队列')

    def send_msg(self):
        msg = self.textEdit.toPlainText().strip()

        if not msg:
            return
        request_dic = RequestData.chat_dic(self.client.user, msg, self.client.token)

        self.request_q.put(request_dic)

    def over(self):
        self.my_thead.terminate()
        QMessageBox.warning(self, '提示', '连接服务器失败，即将关闭程序')
        exit()

    def show_tip(self):
        self.tip_label.setText('连接断开 正在重连...')
        self.tip_label.adjustSize()
        self.tip_label.setFixedSize(self.tip_label.size())
        self.tip_label.show()

        QMessageBox.about(self, '提示', '链接异常正在重连')
        time.sleep(1)
        #  三行代码有小问题
        # x = self.geometry().center().x()
        # y = self.geometry().center().y()
        # self.tip_label.move(x - self.tip_label.width() / 2, y - self.tip_label.height() / 2)

    def t_signal(self, s):
        self.signal_route.get(s)()

    def dic_handle(self, response_dic):
        LOGGER.debug(f'服务器返回的字典  \n{response_dic}')
        fn = self.route_mode.get(response_dic.get('mode'))
        fn(response_dic)

    def append_time(self, local_time):
        if (local_time - self.last_time).total_seconds() > 300:
            cursor = self.textBrowser.textCursor()
            # 光标移动到最后一行
            cursor.movePosition(cursor.MoveOperation.End)
            self.textBrowser.setTextCursor(cursor)
            self.textBrowser.insertHtml(
                f"""
                <tr style="text-align:center">
                    <p>
                        <a class="one_a" style='color:#b2bec3;size:9px'>{local_time}</a>
                    </p>
                </tr>
                """)
            self.last_time = local_time

    def cursor_end(self):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.textBrowser.setTextCursor(cursor)

    def show_file(self, response_dic, align):
        self.cursor_end()
        user = response_dic.get('user')
        url = response_dic.get('file_path')
        html = """
                                        <tr style="text-align:{}">
                                        <p>
                                        <a style="color:{}">{}</a>
                                        <br>
                                        <a href="file://{}">
                                        <img src="{}" width={}>
                                        </a>
                                        {}
                                        </p>
                                        </tr>
                                        """

        if url.split('.')[-1] in IMGS_TYPES:
            # 图片展示
            img_width = QImage(url).width()
            if img_width > 200:
                img_width = 200
            url = url.replace('\\', '/')
            self.textBrowser.insertHtml(html.format(align, USER_COLOR, user, url, url, img_width, ''))
        else:
            # 文件展示
            icon_path = self.get_icon(url)
            file_info_html = """
                                    <br>
                                    <a href="file://{}">【打开文件夹】</a>
                                    <a href="file://{}">{} ({})</a>
                                """
            file_dir = os.path.dirname(url)
            file_dir = file_dir.replace('\\', '/')

            url = url.replace('\\', '/')
            file_name = response_dic.get('file_name')
            file_size = byte_to_human(response_dic.get('file_size'))
            self.textBrowser.insertHtml(html.format(
                align,
                USER_COLOR,
                user,
                url,
                icon_path,
                100,
                file_info_html.format(file_dir, url, file_name, file_size)))

        LOGGER.info('{}发送了文件：{}'.format(user, url))
        self.cursor_end()

    def file_res(self, response_dic, *args, **kwargs):
        # 图片展示
        utc_time = response_dic.get('time')
        local_time = utc_time.astimezone().replace(tzinfo=None)
        self.append_time(local_time)
        self.show_file(response_dic, 'left')

    def chat_res(self, response_dic, *args, **kwargs):
        # 展示到聊天界面
        self.cursor_end()
        user = response_dic.get('user')
        msg = response_dic.get('msg')
        utc_time = response_dic.get('time')
        local_time = utc_time.astimezone().replace(tzinfo=None)

        self.append_time(local_time)
        self.textBrowser.insertHtml(
            f"""
            <tr style="text-align:left">
                <p>
                    <a class="one_a" style='color:{OTHER_USER_COLOR};size:{FONT_NAME_SIZE}'>{user}</a>
                    <br />
                    <a class="two_a" style='background-color:{OTHER_BCK_COLOR};border-radius: 5px;' >{msg}</a>
                </p>
            </tr>
            """)
        LOGGER.info('{}说：{}'.format(user, msg))
        self.cursor_end()

    def reconnect_res(self, response_dic, *args, **kwargs):
        code = response_dic.get('code')
        if code != 200:
            QMessageBox.warning(self, '提示', '{}\n状态码'.format(
                response_dic.get('msg'), code
            ))
            self.login_window.show()
            self.close()
            return

        users = response_dic.get('users')
        self.set_online_users(users)

    def close_broadcast(self):
        # 隐藏标签
        self.label.close()
        self.timer.stop()

    def broadcast_res(self, response_dic, *args, **kwargs):
        LOGGER.debug('broadcast_res', response_dic)
        user = response_dic.get('user')
        if response_dic.get('status') == RESPONSE_ONLINE:
            # 解决重复多次重连、线程数据重复发送问题、如果有相同的广播名就忽略
            if self.listWidget.findItems(user, Qt.MatchFlag.MatchExactly):
                # 有重复值就直接返回不添加
                return

            item = QListWidgetItem()
            self.listWidget.addItem(item)
            if user == self.client.user:
                user = '我'
            item.setText(self._translate("Form", user))
            self.label_3.setText("在线用户数：{}".format(self.listWidget.count()))
            # 弹出广播消息
            self.label.show()
            self.label.setText('{} 进入了聊天室'.format(user))
            LOGGER.debug('{} 进入了聊天室'.format(user))
        # 下线
        else:
            """
            QtCore.Qt.MatchFlag.MatchContains：表示在项中查找包含指定文本的任何部分的项
            QtCore.Qt.MatchFlag.MatchExactly：仅匹配与指定文本完全相同的项
            QtCore.Qt.MatchFlag.MatchStartsWith：仅匹配以指定文本开头的项
            QtCore.Qt.MatchFlag.MatchEndsWith：仅匹配以指定文本结尾的项
            """
            item = self.listWidget.findItems(user, Qt.MatchFlag.MatchExactly)[0]
            # 删除列表项（获取索引然后删除）
            self.listWidget.takeItem(self.listWidget.row(item))
            item.setText(self._translate("Form", user))
            self.label_3.setText("在线用户数：{}".format(self.listWidget.count()))
            # 弹出广播消息
            self.label.show()
            self.label.setText('{} l离开了聊天室'.format(user))
            LOGGER.debug('{} 进入了聊天室'.format(user))
        self.timer.start(4000)

    def set_online_users(self, users):
        # 渲染在线用户
        LOGGER.debug(f'渲染在线用户方法启用！！ {users}')
        self.listWidget.clear()
        self.label_3.setText("在线用户数：{}".format(len(users)))
        for user in users:
            item = QListWidgetItem()
            self.listWidget.addItem(item)
            if user == self.client.user:
                user = '我'
            item.setText(self._translate("Form", user))


class MyThread(QThread):
    # 实例化信号、子线程无法调用主线程里面的qt控件、只能通过信号让主线程帮忙
    reconnected = pyqtSignal(str)
    received = pyqtSignal(dict)
    send_success = pyqtSignal(dict)

    def __init__(self, client, request_q=None):
        self.client = client
        self.request_q = request_q
        super().__init__()

    def run(self):
        if self.request_q:
            self.loop_send()
            return
        self.loop_recv()

    @reconnect_t
    def get(self):
        return self.client.recv_data()

    @reconnect_t
    def put(self, dic):
        self.client.send_data(dic)
        return True

    def loop_recv(self):
        LOGGER.debug('接收数据')
        while True:
            response_dic = self.get()
            LOGGER.debug(response_dic)
            if not response_dic:
                # 重连成功，发重连请求更新数据
                while True:
                    request_dic = RequestData.reconnect_dic(self.client.user, self.client.token)
                    if not self.put(request_dic):
                        continue
                    LOGGER.info('重连字典发送成功')
                    break
                continue
            LOGGER.debug('链接正常')
            LOGGER.debug(f'response_dic   {response_dic}')
            LOGGER.debug('广播数据')
            self.received.emit(response_dic)

    def loop_send(self):
        while True:
            request_dic = self.request_q.get()
            url = request_dic.get('file_path')
            if not self.put(request_dic):
                # 发送失败重连成功
                return
            # 发送成功
            request_dic['file_path'] = url
            self.send_success.emit(request_dic)


def run():
    import sys
    # 连接服务器
    with MySocket(HOST, PORT) as client:
        # 展示登录界面
        app = QApplication(sys.argv)
        login_window = LoginWindow(client)
        login_window.show()

        sys.exit(app.exec())
