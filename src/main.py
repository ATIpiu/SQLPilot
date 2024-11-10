import json
import os
import sys
from datetime import datetime
from functools import partial

import erniebot
import yaml
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QWidget, QApplication
from qfluentwidgets import (
    NavigationItemPosition, MessageBox, MSFluentWindow, FluentIcon as FIF
)

from src.database.DatabaseTool import DatabaseTool
from src.ui.Chat import ChatWidget


class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()

        # 初始化数据库工具
        self.db_tool = DatabaseTool(db_path="test.db")

        # 加载历史聊天记录
        self.chatHistories = self.load_chat_histories()

        # 创建聊天界面
        self.chatInterface = ChatWidget(db_tool=self.db_tool, parent=self)
        self.chatInterface.setObjectName("new_chat")  # 确保有唯一的 objectName
        self.stackedWidget.addWidget(self.chatInterface)

        self.currentChatTitle = "new_chat"  # 记录当前聊天标题
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        # 使用 addItem 添加“新建聊天”选项
        self.navigationInterface.addItem(
            routeKey='new_chat',
            icon=FIF.ADD,  # 新建聊天图标
            text='新建聊天',
            onClick=self.newChatClicked
        )

        self.renderChatHistories()

        # 添加帮助项
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        # 默认选中“新建聊天”
        self.navigationInterface.setCurrentItem("new_chat")

    def load_chat_histories(self, file_path='chat_histories.json'):
        """从文件加载历史聊天记录并将日期字符串转换为 datetime 对象"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                chat_histories = json.load(file)

            # 将日期字符串转换为 datetime 对象
            for chat_title, history in chat_histories.items():
                for record in history:
                    record["date"] = datetime.strptime(record["date"], "%Y-%m-%d %H:%M:%S.%f")

            return chat_histories
        return {}

    def save_chat_histories(self, file_path='chat_histories.json'):
        """将聊天记录保存到文件"""
        if len(self.chatInterface.chat_history)!=0:
            self.chatHistories[self.chatInterface.chat_history[0]['content'][0:5]] = self.chatInterface.chat_history
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(self.chatHistories, file, ensure_ascii=False, indent=4, default=str)

    def closeEvent(self, event):
        """在窗口关闭时保存聊天记录"""
        self.save_chat_histories()
        super().closeEvent(event)

    def renderChatHistories(self):
        # 按最新修改时间排序
        sorted_chats = sorted(
            self.chatHistories.items(),
            key=lambda x: x[1][-1]["date"],  # 此时 date 已是 datetime 对象
            reverse=True
        )

        # 删除所有已有导航项
        for key in list(self.chatHistories.keys()):
            self.navigationInterface.removeWidget(routeKey=key)

        # 重新渲染导航项
        for chat_title, history in sorted_chats:
            last_message_time = history[-1]["date"].strftime("%Y-%m-%d %H:%M:%S")
            self.navigationInterface.addItem(
                routeKey=chat_title,
                icon=FIF.CHAT,
                text=f"{chat_title} ",
                onClick=partial(self.chat_changed, chat_title)
            )

    def chat_changed(self, chat_title):
        # 更新当前聊天标题并加载聊天记录
        self.currentChatTitle = chat_title
        new = self.chatInterface.set_chat_history((chat_title, self.chatHistories.get(chat_title, [])))
        if new and new[0].startswith("new_chat") and len(new[1])!=0:
            self.chatHistories[new[1][0]['content'][0:5]] = new[1]

        self.renderChatHistories()

    def newChatClicked(self):
        if self.currentChatTitle == "new_chat":
            self.currentChatTitle = "new_chat1"
        else:
            self.currentChatTitle = "new_chat"
        if len(self.chatInterface.chat_history)!=0:
            self.chatHistories[self.chatInterface.chat_history[0]['content'][0:5]] = self.chatInterface.chat_history
        self.renderChatHistories()
        self.chatInterface.set_chat_history((self.currentChatTitle, self.chatHistories.get(self.currentChatTitle, [])))
        self.switchTo(self.chatInterface)

    def switchTo(self, interface: QWidget):
        self.chatInterface.renderChatHistory()
        self.stackedWidget.setCurrentWidget(interface)

    def loadChatHistory(self, title):
        """
        加载历史聊天记录到 ChatWidget.
        """
        # 保存当前聊天记录
        if self.currentChatTitle != "new_chat":
            self.chatHistories[self.currentChatTitle] = self.chatInterface.chat_history

        # 更新当前聊天标题并加载聊天记录
        self.currentChatTitle = title
        self.chatInterface.chat_history = self.chatHistories.get(title, [])
        self.chatInterface.renderChatHistory()

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://qfluentwidgets.com/zh/price/"))

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('SQLpilot')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def load_config(self, config_path='config.yaml'):
        """加载配置文件"""
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            erniebot.access_token = config['erniebot']['access_token']




if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()