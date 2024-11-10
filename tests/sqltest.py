import sqlite3

import erniebot
import yaml

with open('../config/config.yaml',encoding='utf-8') as file:
    config = yaml.safe_load(file)
    erniebot.api_type = 'aistudio'
    erniebot.access_token = config['erniebot']['access_token']

class DatabaseTool:
    def __init__(self, db_path):
        self.db_path = db_path

    def validate_and_execute(self, sql_query):
        """使用大模型验证SQL语句合法性，确保只有一句并执行"""

        # 调用大模型验证SQL合法性并确保只有一句
        response = erniebot.ChatCompletion.create(
            model='ernie-4.0',
            system='你是一个只能sql助手，只能返回sql语句，不能返回其他内容。',
            messages=[
                {"role": "user",
                 "content": f"以下是用户提供的SQL语句：{sql_query}。确保返回一条合法的、仅包含一句的SQL语句。如果用户提供了多条，请修改为合法的一句。"}
            ]
        )

        # 获取验证后的SQL语句
        validated_sql = response.get_result()
        print(validated_sql)
        # 执行验证后的SQL
        return self._execute_sql(validated_sql)

    def _execute_sql(self, sql_query):
        """执行SQL语句并返回结果"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()

            if sql_query.strip().lower().startswith("select"):
                results = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                return {"columns": column_names, "data": results}
            return "操作成功"
        except Exception as e:
            return f"SQL执行错误: {str(e)}"
        finally:
            connection.close()
db_tool = DatabaseTool("example.db")

# 示例1：多条SQL语句输入
query = "SELECT * FROM users; DELETE FROM users WHERE id = 1;"
print(db_tool.validate_and_execute(query))  # 返回大模型处理后的合法SQL执行结果

# 示例2：单条SQL语句输入
query = "SELECT * FROM users;"
print(db_tool.validate_and_execute(query))  # 返回查询结果
