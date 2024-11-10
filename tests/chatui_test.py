import sys
from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QVBoxLayout, QScrollArea,
      QWidget
)
from qfluentwidgets import (
    NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
    NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, LineEdit, SingleDirectionScrollArea, NavigationBar
)
from qfluentwidgets import FluentIcon as FIF


from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from qfluentwidgets import SubtitleLabel, setFont


class ChatBubble(QFrame):
    def __init__(self, is_mine, content_type, content, date, parent=None):
        super().__init__(parent)
        self.is_mine = is_mine
        self.content_type = content_type
        self.content = content

        # 创建日期标签
        date_label = QLabel(f"{date:%Y-%m-%d %H:%M:%S}", self)
        date_label.setStyleSheet("color: gray; font-size: 12px;")  # 字体稍大
        date_label.setAlignment(Qt.AlignCenter)  # 上下居中

        # 创建内容标签
        content_label = SubtitleLabel(self)
        content_label.setWordWrap(True)

        if content_type == "text":
            content_label.setText(content)
        elif content_type == "image":
            pixmap = QPixmap(content).scaled(200, 200, Qt.KeepAspectRatio)
            content_label.setPixmap(pixmap)
        else:
            content_label.setText("Unsupported content type.")

        if is_mine:
            content_label.setStyleSheet("background-color: #E1E1E1; border-radius: 8px; padding: 10px;")
        else:
            content_label.setStyleSheet("background-color: #ADD8E6; border-radius: 10px; padding: 8px;")

        # 布局调整
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        # 根据消息归属调整布局内容
        if is_mine:
            # 用户消息：日期标签在左，内容气泡在右
            self.layout.addWidget(date_label, alignment=Qt.AlignVCenter)
            self.layout.addWidget(content_label)
            self.layout.setAlignment(Qt.AlignRight)
        else:
            # 系统消息：内容气泡在左，日期标签在右
            self.layout.addWidget(content_label)
            self.layout.addWidget(date_label, alignment=Qt.AlignVCenter)
            self.layout.setAlignment(Qt.AlignLeft)



class ChatWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatInterface")

        # 设置整体样式：圆角、无边框、纯白背景
        self.setStyleSheet("""
            QFrame#ChatInterface {
                background-color: white;
                border: none;
                border-radius: 15px;
            }
            QLineEdit {
                background-color: #F5F5F5;
                border: none;
                border-radius: 10px;
                padding-left: 10px;
                font-size: 14px;
            }
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        self.chat_title=""
        self.chat_history = []  # 聊天记录列表
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        # 聊天记录显示区域
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setSpacing(10)
        self.scrollArea.setWidget(self.scrollContent)

        # 输入框区域
        inputLayout = QHBoxLayout()
        self.inputField = LineEdit(self)
        self.inputField.setPlaceholderText("输入消息...")
        self.inputField.setFixedHeight(40)
        self.inputField.setFont(QFont("Arial", 14))
        self.inputField.returnPressed.connect(self.sendMessage)

        inputLayout.addWidget(self.inputField)

        # 添加到主布局
        self.layout.addWidget(self.scrollArea, stretch=1)
        self.layout.addLayout(inputLayout)

        # 渲染初始聊天记录
        self.renderChatHistory()

    def addChatRecord(self, is_mine, content_type, content):
        chat_record = {
            "is_mine": is_mine,
            "type": content_type,
            "content": content,
            'date': datetime.now()
        }
        self.chat_history.append(chat_record)
        self.renderChatHistory()

    def renderChatHistory(self):
        # 清除现有的聊天记录显示
        for i in reversed(range(self.scrollLayout.count())):
            widget_to_remove = self.scrollLayout.itemAt(i).widget()
            if widget_to_remove:
                self.scrollLayout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()

        # 渲染聊天记录
        for record in self.chat_history:
            bubble = ChatBubble(
                record["is_mine"],
                record["type"],
                record["content"],
                record["date"],
                self.scrollContent
            )
            self.scrollLayout.addWidget(bubble)

        # 滚动到底部
        self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        )

    def sendMessage(self):
        content = self.inputField.text().strip()
        if content:
            self.addChatRecord(True, "text", content)
            self.inputField.clear()
            # 模拟对方回复
            self.addChatRecord(False, "text", "这是对方的回复消息。")

    def set_chat_history(self, chat_history):
        print("传入的聊天历史记录：", chat_history)
        print("当前聊天标题：", self.chat_title)
        print("当前聊天历史记录：", self.chat_history)
        if self.chat_title!= chat_history[0]:
            if len(self.chat_history)!=0:
                old_chat_title, old_chat_history = self.chat_title, self.chat_history
                self.chat_title, self.chat_history = chat_history[0], chat_history[1]
                return old_chat_title, old_chat_history
            else:
                self.chat_title = chat_history[0]
                self.chat_history = chat_history[1]
                self.renderChatHistory()
                return None







class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()

        # 创建聊天界面
        self.chatInterface = ChatWidget(self)
        self.chatInterface.setObjectName("new_chat")  # 确保有唯一的 objectName
        self.stackedWidget.addWidget(self.chatInterface)
        # 存储历史聊天的元数据
        self.chatHistories = {
            "聊天记录 12312311": [
                {"is_mine": True, "type": "text", "content": "Hello!", "date": datetime(2023, 11, 1, 10, 0)},
                {"is_mine": False, "type": "text", "content": "这是之前的聊天记录。",
                 "date": datetime(2023, 11, 1, 10, 5)}
            ],
            "聊天记录 2": [
                {"is_mine": True, "type": "text", "content": "Hello!", "date": datetime(2024, 11, 1, 10, 0)},
                {"is_mine": False, "type": "text", "content": "这是之前的聊天记录。",
                 "date": datetime(2024, 11, 1, 10, 5)}
            ]
        }

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


    def renderChatHistories(self):
        # 按最新修改时间排序
        sorted_chats = sorted(
            self.chatHistories.items(),
            key=lambda x: x[1][-1]["date"],
            reverse=True
        )
        print(sorted_chats)
        for key in list(self.chatHistories.keys()):
            self.navigationInterface.removeWidget(routeKey=key)
        # 重新渲染导航项
        for chat_title, history in sorted_chats:
            # last_message_time = history[-1]["date"].strftime("%Y-%m-%d %H:%M:%S")
            self.navigationInterface.addItem(
                routeKey=chat_title,
                icon=FIF.CHAT,
                text=f"{chat_title} ",
                onClick=partial(self.chat_changed, chat_title)
            )

    def chat_changed(self, chat_title):
            # 更新当前聊天标题并加载聊天记录
        self.currentChatTitle = chat_title
        new=self.chatInterface.set_chat_history((chat_title,self.chatHistories.get(chat_title, [])))
        if new and new[0]=='new_chat':
            self.chatHistories[new[1][0]['content'][0:10]]=new[1]
        self.renderChatHistories()
        print(self.chatHistories)
    def newChatClicked(self):
        self.currentChatTitle = "new_chat"
        self.chatInterface.set_chat_history(("new_chat", self.chatHistories.get("new_chat", [])))
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
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://qfluentwidgets.com/zh/price/"))

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('聊天窗口 - PyQt-Fluent-Widgets')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
