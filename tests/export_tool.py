import sqlite3

class DatabaseTool:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_structure_as_string(self):
        """仅获取数据库结构（不包含数据）并返回为字符串"""
        try:
            connection = sqlite3.connect(self.db_path)
            structure = []
            for line in connection.iterdump():
                # 过滤掉包含 INSERT INTO 的语句
                if not line.startswith("INSERT INTO"):
                    structure.append(line)
            connection.close()
            return '\n'.join(structure)
        except Exception as e:
            return f"获取数据库结构时发生错误: {str(e)}"

# 使用示例
# 准备数据库
db_path = "test.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()
create_table_query = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"
cursor.execute(create_table_query)
# 插入测试数据
insert_query = "INSERT INTO users (id, name, age) VALUES (?,?,?)"
test_data = [
    (1, 'Tom', 30),
    (2, 'Bob', 25),
    (3, 'Alice', 35)
]
cursor.executemany(insert_query, test_data)

connection.commit()
connection.close()

db_tool = DatabaseTool("test.db")
structure = db_tool.get_structure_as_string()
print(structure)
