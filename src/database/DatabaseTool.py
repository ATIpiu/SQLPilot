import os
import sqlite3
import csv
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams


class DatabaseTool:
    def __init__(self, db_path):
        self.db_path = db_path

    def insert(self, sql_query, table_name):
        """插入数据后返回表的所有数据"""
        return self._execute_and_return_table(sql_query, table_name)

    def update(self, sql_query, table_name):
        """更新数据后返回表的所有数据"""
        return self._execute_and_return_table(sql_query, table_name)

    def delete(self, sql_query, table_name):
        """删除数据后返回表的所有数据"""
        return self._execute_and_return_table(sql_query, table_name)

    def create_table(self, query):
        """创建表"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return "表已成功创建。"
        except Exception as e:
            return f"创建表失败: {str(e)}"
        finally:
            connection.close()

    def drop_table(self, table_name):
        """删除表"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            connection.commit()
            return f"表 {table_name} 已成功删除。"
        except Exception as e:
            return f"删除表失败: {str(e)}",[]
        finally:
            connection.close()

    def truncate_table(self, table_name):
        """清空表"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM {table_name}")
            connection.commit()
            return f"表 {table_name} 已成功清空。"
        except Exception as e:
            return f"清空表失败: {str(e)}",[]
        finally:
            connection.close()

    def select(self, sql_query):
        """查询数据并返回结果"""
        print(f"执行查询: {sql_query}")
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # 获取列名
            column_names = [description[0] for description in cursor.description]

            if results:
                # 格式化查询结果为文本
                result_text = "\n".join([", ".join(map(str, row)) for row in results])
                return (
                    f"列名: {', '.join(column_names)}\n{result_text}",
                    {"columns": column_names, "data": results}
                )
            else:
                return "查询无结果", {"columns": column_names, "data": []}
        except Exception as e:
            return f"数据库错误: {str(e)}", {"columns": [], "data": []}
        finally:
            connection.close()

    def _execute_and_return_table(self, sql_query, table_name):
        """执行增、删、改操作后，返回对应表的所有数据以及列名"""
        print(f"执行SQL操作: {sql_query}")
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            connection.commit()  # 提交增删改操作

            # 查询操作后的完整表数据
            full_table_query = f"SELECT * FROM {table_name}"
            cursor.execute(full_table_query)
            results = cursor.fetchall()

            # 获取列名
            column_names = [description[0] for description in cursor.description]

            if results:
                # 格式化输出
                result_text = "\n".join([", ".join(map(str, row)) for row in results])
                print(results)
                return f"列名: {', '.join(column_names)}\n{result_text}", {"columns": column_names, "data": results}
            else:
                return f"表 {table_name} 当前无数据", {"columns": column_names, "data": []}
        except Exception as e:
            return f"数据库错误: {str(e)}", {"columns": [], "data": []}
        finally:
            connection.close()

    def get_structure_as_string(self):
        """仅获取数据库结构（不包含数据）并返回为字符串"""
        try:
            connection = sqlite3.connect(self.db_path)
            structure = []
            for line in connection.iterdump():
                if not line.startswith("INSERT INTO"):
                    structure.append(line)
            connection.close()
            return '\n'.join(structure)
        except Exception as e:
            return f"获取数据库结构时发生错误: {str(e)}"

    def export_to_csv(self, table_name, file_name):
        """将指定表导出为CSV文件"""
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

    def plot_data_from_db(self, table_name, column_name, plot_type):
        """从数据库绘制分布图或折线图，并保存图片"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(f"SELECT {column_name} FROM {table_name}")
            data = [row[0] for row in cursor.fetchall()]
            connection.close()

            if not data:
                return f"表 {table_name} 的列 {column_name} 无数据或获取失败。", ""

            # 生成图片路径
            image_dir = "plots"
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"{table_name}_{column_name}_{plot_type}.png")

            rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
            rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

            # 绘图
            plt.figure(figsize=(6, 4))
            if plot_type == 'hist':
                plt.hist(data, bins=20, color='skyblue', edgecolor='black')
                plt.title(f"分布图 - {table_name} - {column_name}")
                plt.xlabel('值')
                plt.ylabel('频数')
            elif plot_type == 'line':
                plt.plot(data, marker='o', linestyle='-', color='blue')
                plt.title(f"折线图 - {table_name} - {column_name}")
                plt.xlabel('索引')
                plt.ylabel('值')
            else:
                return "不支持的绘图类型。", ""

            plt.tight_layout()
            plt.savefig(image_path)
            plt.close()

            return f"{plot_type.capitalize()} 图已生成：表 {table_name} 的列 {column_name}。", image_path

        except Exception as e:
            return f"绘图失败：{str(e)}", ""

    def export_to_sql(self, file_name, include_data):
        """导出数据库结构及可选的数据内容为SQL文件"""
        try:
            connection = sqlite3.connect(self.db_path)
            with open(file_name, 'w', encoding='utf-8') as file:
                for line in connection.iterdump():
                    if include_data != 1 and line.startswith("INSERT INTO"):
                        continue
                    file.write(f"{line}\n")
            connection.close()
            return f"数据库已成功导出到 {file_name}，包含数据: {bool(include_data)}"
        except Exception as e:
            return f"导出SQL时发生错误: {str(e)}"