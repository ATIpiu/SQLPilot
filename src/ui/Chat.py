from datetime import datetime

import erniebot
import yaml
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QScrollArea, QWidget, QSizePolicy
from qfluentwidgets import LineEdit
from PyQt5.QtWidgets import QFrame, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import json

class QueryThread(QThread):
    result_ready = pyqtSignal(object)  # 改为通用类型
    error = pyqtSignal(str)

    def __init__(self, db_tool, sql_str, messages, parent=None):
        super().__init__(parent)
        self.db_tool = db_tool
        self.sql_str = sql_str
        self.messages = messages
        print('sql_str', self.sql_str)

    def run(self):
        try:
            # 调用 ErnieBot 进行处理
            response = erniebot.ChatCompletion.create(
                model='ernie-4.0',
                messages=self.messages,
                system='你是一个智能数据库助手，这是数据库的sql语句' + self.sql_str+',尽可能使用单句sql完成操作,数据库的列名必须是英文,不需要解释',
                functions=[
                    {
                        'name': 'data_option',
                        'description': "执行数据操作，包括插入、更新、删除和查询。",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'operation': {
                                    'type': 'string',
                                    'enum': ['insert', 'update', 'delete', 'select'],  # 操作类型
                                    'description': '操作类型，可选值: insert, update, delete, select'
                                },
                                'query': {
                                    'type': 'string',
                                    'description': 'SQL查询语句'
                                },
                                'table_name': {
                                    'type': 'string',
                                    'description': '操作的表名（对于select可为空）',
                                    'default': ''
                                }
                            },
                            'required': ['operation', 'query']
                        }
                    },
                    {
                        'name': 'create_table',
                        'description': "创建新表，使用指定的SQL语句。",
                        'parameters': {
                            'type': 'object',
                            'properties': {

                                'query': {
                                    'type': 'string',
                                    'description': '创建表的完整SQL语句',
                                }
                            },
                            'required': [ 'query']
                        }
                    },
                    {
                        'name': 'drop_table',
                        'description': "删除指定的表。",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'table_name': {
                                    'type': 'string',
                                    'description': '要删除的表名'
                                }
                            },
                            'required': ['table_name']
                        }
                    },
                    {
                        'name': 'export_csv',
                        'description': "将指定表导出为CSV文件。",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'table_name': {'type': 'string'},
                                'file_name': {'type': 'string'}
                            },
                            'required': ['table_name', 'file_name']
                        }
                    },
                    {
                        'name': 'plot_data',
                        'description': "从指定表中选取一列数据，绘制分布图或折线图。",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'table_name': {'type': 'string'},
                                'column_name': {'type': 'string'},
                                'plot_type': {'type': 'string', 'enum': ['hist', 'line']}  # 支持分布图和折线图
                            },
                            'required': ['table_name', 'column_name', 'plot_type']
                        }
                    },
                    {
                        'name': 'export_sql',
                        'description': "将数据库结构以及可选的数据内容导出为SQL文件。",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'file_name': {'type': 'string'},
                                'include_data': {'type': 'int'}  # 是否包含数据内容
                            },
                            'required': ['file_name', 'include_data']
                        }
                    }
                ]
            )

            if response.is_function_response:
                function_call = response.get_result()
                self.result_ready.emit(function_call)
            else:
                self.result_ready.emit(response.get_result())
        except Exception as e:
            print(e)
            self.error.emit(str(e))


class ChatBubble(QFrame):
    def __init__(self, is_mine, content_type, content, date, parent=None):
        super().__init__(parent)
        self.is_mine = is_mine
        self.content_type = content_type
        self.content = content

        # 创建日期标签
        date_label = QLabel(f"{date:%Y-%m-%d %H:%M:%S}", self)
        date_label.setStyleSheet("color: gray; font-size: 12px;")
        date_label.setAlignment(Qt.AlignCenter)

        # 根据内容类型创建不同的内容组件
        if content_type == "text" or content_type == "table":
            content_label = QTextEdit(self)
            content_label.setReadOnly(True)  # 只读
            content_label.setStyleSheet(
                "background-color: #ADD8E6; border-radius: 10px; padding: 8px;"
                if not is_mine else
                "background-color: #E1E1E1; border-radius: 8px; padding: 10px;"
            )

            if not is_mine:
                # 不是我的消息，使用Markdown渲染
                markdown_content = self.convert_to_markdown(content_type, content)
                content_label.setMarkdown(markdown_content)
            else:
                # 是我的消息，直接显示文本
                content_label.setPlainText(content)

            content_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            content_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            # 动态调整尺寸
            content_label.document().setTextWidth(content_label.viewport().width())
            content_label.setFixedHeight(
                int(content_label.document().size().height() + content_label.frameWidth() +10)
            )


        elif content_type == "image":
            content_label = QLabel(self)
            pixmap = QPixmap(content)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                content_label.setPixmap(scaled_pixmap)
                content_label.setStyleSheet(
                    "border: 1px solid #ccc; border-radius: 8px; padding: 5px;"
                )
                content_label.setFixedSize(scaled_pixmap.size())  # 根据图片大小调整气泡
            else:
                content_label.setText("图片加载失败")
                content_label.setStyleSheet("color: red;")

        else:
            content_label = QLabel("Unsupported content type.", self)
            content_label.setStyleSheet("color: red;")

        # 布局调整
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        # 添加内容布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(5)

        if is_mine:
            content_layout.addWidget(date_label, alignment=Qt.AlignVCenter)
            content_layout.addWidget(content_label)
            content_layout.setAlignment(Qt.AlignRight)
        else:
            content_layout.addWidget(content_label)
            content_layout.addWidget(date_label, alignment=Qt.AlignVCenter)
            content_layout.setAlignment(Qt.AlignLeft)

        self.layout.addLayout(content_layout)

    def convert_to_markdown(self, content_type, content):
        """将不同类型的内容转化为Markdown格式"""
        if content_type == "text":
            return content

        elif content_type == "table":
            table_info = json.loads(content)
            columns = table_info.get("columns", [])
            rows = table_info.get("data", [])

            if not columns:
                return "表格数据无列名"

            markdown_table = "| " + " | ".join(columns) + " |\n"
            markdown_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"
            for row in rows:
                markdown_table += "| " + " | ".join(map(str, row)) + " |\n"

            return markdown_table

        return "Unsupported content type."

class ChatWidget(QFrame):
    def __init__(self, db_tool, config_path='../config/config.yaml', parent=None):
        super().__init__(parent)
        self.db_tool = db_tool
        self.sql_str = db_tool.get_structure_as_string()
        self.setObjectName("ChatInterface")

        # 读取配置文件
        self.load_config(config_path)

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
        self.chat_title = ""
        self.chat_history = []  # 聊天记录列表
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        self.layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)

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

    def load_config(self, config_path):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            erniebot.api_type = 'aistudio'
            erniebot.access_token = config['erniebot']['access_token']
            print(config['erniebot']['access_token'])

    def addChatRecord(self, is_mine, content_type, content):
        chat_record = {
            "is_mine": is_mine,
            "type": content_type,
            "content": content,
            'date': datetime.now()
        }
        print(self.chat_history)
        self.chat_history.append(chat_record)
        self.renderChatHistory()

    def set_chat_history(self, chat_history):
        print("传入的聊天历史记录：", chat_history)
        print("当前聊天标题：", self.chat_title)
        print("当前聊天历史记录：", self.chat_history)
        if self.chat_title != chat_history[0]:
            if len(self.chat_history) != 0:
                old_chat_title, old_chat_history = self.chat_title, self.chat_history
                self.chat_title, self.chat_history = chat_history[0], chat_history[1]
                return old_chat_title, old_chat_history
            else:
                self.chat_title = chat_history[0]
                self.chat_history = chat_history[1]
                self.renderChatHistory()
                return None

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
        """处理用户发送的消息并包含历史聊天记录"""
        self.sql_str = self.db_tool.get_structure_as_string()
        content = self.inputField.text().strip()
        if content:
            # 将新消息添加到聊天记录
            self.addChatRecord(True, "text", content)
            self.inputField.clear()

            # 整合历史聊天记录
            messages = self.build_messages(content)

            # 创建线程并启动
            self.query_thread = QueryThread(self.db_tool, self.sql_str, messages)
            self.query_thread.result_ready.connect(self.handleResponse)
            self.query_thread.error.connect(self.handleError)
            self.query_thread.start()

    def handleResponse(self, response):
        """处理线程返回的结果"""
        if isinstance(response, dict):
            function_name = response.get('name')
            arguments = json.loads(response['arguments'])

            if function_name == 'data_option':
                operation = arguments['operation']
                query = arguments['query']
                table_name = arguments.get('table_name', '')

                if operation in ['insert', 'update', 'delete']:
                    result_message, results = self.db_tool._execute_and_return_table(query, table_name)
                    self.addChatRecord(False, "text", f"{operation.capitalize()} 操作成功。\n{result_message}")
                    self.addChatRecord(False, "table", json.dumps(results))
                elif operation == 'select':
                    result_message, results = self.db_tool.select(query)
                    self.addChatRecord(False, "text", result_message)
                    self.addChatRecord(False, "table", json.dumps(results))

            elif function_name == 'create_table':


                query = arguments['query']

                result_message = self.db_tool.create_table(query)

                self.addChatRecord(False, "text", result_message)

            elif function_name == 'drop_table':

                table_name = arguments['table_name']

                result_message = self.db_tool.drop_table(table_name)

                self.addChatRecord(False, "text", result_message)


            elif function_name == 'truncate_table':

                table_name = arguments['table_name']

                result_message = self.db_tool.truncate_table(table_name)

                self.addChatRecord(False, "text", result_message)

            elif function_name == 'export_csv':
                table_name = arguments['table_name']
                file_name = arguments['file_name']
                result_message = self.db_tool.export_to_csv(table_name, file_name)
                self.addChatRecord(False, "text", result_message)

            elif function_name == 'export_sql':
                file_name = arguments['file_name']
                include_data = arguments['include_data']  # 获取int类型的include_data
                result_message = self.db_tool.export_to_sql(file_name, include_data)
                self.addChatRecord(False, "text", result_message)

            elif function_name == 'plot_data':
                table_name = arguments['table_name']
                column_name = arguments['column_name']
                plot_type = arguments['plot_type']
                result_message, image_path = self.db_tool.plot_data_from_db(table_name, column_name, plot_type)
                self.addChatRecord(False, "text", result_message)
                self.addChatRecord(False, "image", image_path)

            else:
                self.addChatRecord(False, "text", f"未知操作: {function_name}")
        else:
            self.addChatRecord(False, "text", str(response))

    def handleError(self, error_message):
        """处理线程中出现的错误"""
        self.addChatRecord(False, "text", f"Error: {error_message}")

    def build_messages(self, new_message):
        """构建包含历史记录的消息列表"""
        messages = []
        # for record in self.chat_history:
        #     role = 'user' if record['is_mine'] else 'assistant'
        #     messages.append({'role': role, 'content': record['content']})

        # 添加当前用户输入
        messages.append({'role': 'user', 'content': new_message})
        return messages
    #
    # def process_query(self, messages):
    #     """与 ErnieBot 和数据库交互"""
    #     response = erniebot.ChatCompletion.create(
    #         model='ernie-3.5',
    #         messages=messages,
    #         system='你是一个智能数据库助手，这是数据库的sql语句，请你协助我完成各种操作尽可能使用一句sql完成操作,' + self.sql_str,
    #         functions=[
    #             {
    #                 'name': 'query_database',
    #                 'description': "通过SQL查询数据库。如果有返回结果则fetch_results=1,否则为0",
    #                 'parameters': {
    #                     'type': 'object',
    #                     'properties': {'query': {'type': 'string'}, 'fetch_results': {'type': 'integer'}},
    #                     'required': ['query', "fetch_results"]
    #                 }
    #             },
    #             {
    #                 'name': 'export_csv',
    #                 'description': "将指定表导出为CSV文件。",
    #                 'parameters': {
    #                     'type': 'object',
    #                     'properties': {
    #                         'table_name': {'type': 'string'},
    #                         'file_name': {'type': 'string'}
    #                     },
    #                     'required': ['table_name', 'file_name']
    #                 }
    #             }
    #         ]
    #     )
    #     print('res:',response)
    #     if response.is_function_response:
    #         function_call = response.get_result()
    #
    #         if function_call['name'] == 'query_database':
    #             sql_query = json.loads(function_call['arguments'])['query']
    #             fetch_results = json.loads(function_call['arguments'])['fetch_results']
    #             if fetch_results == 1:
    #                 fetch_results = True
    #             else:
    #                 fetch_results = False
    #             return self.db_tool.execute(sql_query, fetch_results)
    #
    #         elif function_call['name'] == 'export_csv':
    #             args = json.loads(function_call['arguments'])
    #             return self.db_tool.export_to_csv(args['table_name'], args['file_name'])
    #
    #     return response.get_result()
