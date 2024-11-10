import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 生成数据
x = np.linspace(0, 10, 100)
y = np.sin(x)

# 创建图形
plt.figure(figsize=(8, 6))

# 绘制折线图
plt.plot(x, y, label='正弦曲线')

# 添加标题和轴标签
plt.title('使用Matplotlib绘制正弦曲线')
plt.xlabel('X轴')
plt.ylabel('Y轴')

# 添加图例
plt.legend()

# 显示图形
plt.show()
