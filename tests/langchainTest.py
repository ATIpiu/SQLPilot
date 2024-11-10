import erniebot
import sqlite3
import csv
import json

# 自定义数据库查询工具
class DatabaseTool:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute(self, sql_query, fetch_results=True):
        print(f"执行SQL查询: {sql_query}")
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            if fetch_results:
                results = cursor.fetchall()
            else:
                connection.commit()
                results = "操作成功"
            connection.close()
            return results
        except Exception as e:
            return f"数据库错误: {str(e)}"

    def export_to_csv(self, table_name, file_name):
        print(f"导出表 {table_name} 到CSV文件 {file_name}")
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                writer.writerows(rows)
            connection.close()
            return f"表 {table_name} 已成功导出到 {file_name}"
        except Exception as e:
            return f"导出CSV时发生错误: {str(e)}"


# 准备数据库
db_path = "../src/test.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()
connection.commit()
connection.close()

# 初始化ERNIE Bot
erniebot.api_type = 'aistudio'
erniebot.access_token = '03a794f63c8002be85524c48337924d4d04634fe'  # 替换为你的Access Token

# 初始化数据库工具
db_tool = DatabaseTool(db_path=db_path)

# 构造对话和工具调用逻辑
def process_query(messages):
    response = erniebot.ChatCompletion.create(
        model='ernie-3.5',
        messages=messages,
        functions=[
            {
                'name': 'query_database',
                'description': "通过SQL查询数据库。",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'SQL查询语句'}
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'export_csv',
                'description': "将指定表导出为CSV文件。",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'table_name': {'type': 'string', 'description': '表名'},
                        'file_name': {'type': 'string', 'description': 'CSV文件名'}
                    },
                    'required': ['table_name', 'file_name']
                }
            }
        ]
    )

    if response.is_function_response:
        # 获取单个函数调用结果
        function_call = response.get_result()
        print(f"模型返回函数调用: {function_call}")
        results = []

        if function_call['name'] == 'query_database':
            sql_query = json.loads(function_call['arguments'])['query']
            query_result = db_tool.execute(sql_query, fetch_results=False)
            results.append(query_result)
            messages.append(response.to_message())

        elif function_call['name'] == 'export_csv':
            args = json.loads(function_call['arguments'])
            export_result = db_tool.export_to_csv(args['table_name'], args['file_name'])
            results.append(export_result)
            messages.append({
                'role': 'function',
                'name': function_call['name'],
                'content': json.dumps({"result": export_result}, ensure_ascii=False),
            })
        return results
    else:
        return response.get_result()

# # 测试：插入和删除组合
# messages = [{'role': 'user', 'content': "我有那些数据表"}]
# result = process_query(messages)
# print(f"操作结果: {result}")
#
# 测试：导出到CSV
messages = [{'role': 'user', 'content': "将users表导出为users.csv文件"}]
result = process_query(messages)
print(f"导出结果: {result}")
