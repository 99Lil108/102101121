import pandas as pd
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt

import matplotlib.font_manager as fm

# 获取系统中已安装的字体列表
font_list = fm.findSystemFonts()

# 打印所有已安装字体的路径,并获取 宋体(SimSun)或是微软雅黑（Microsoft YaHei）
fp = ''
for font_path in font_list:
    path_lower = font_path.lower()
    if 'simsun' in path_lower or 'microsoft yahei' in path_lower:
        fp = font_path
        break

data = pd.read_excel('all_dm.xlsx')  # 打开Excel
sentences = data['content'].tolist()  # 把content列转成list
my_stopwords = ['是', '的', '了', '啊','吗','是','吧','你','就','我']
# 进行分词
words_list = []
for sentence in sentences:
    words = jieba.lcut(str(sentence))
    words_list.extend(words)

# 生成词云
text = ' '.join(words_list)
wordcloud = WordCloud(width=800, height=400, font_path=fp, background_color="white",stopwords=my_stopwords).generate(text)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()
wordcloud.to_file('wordcloud.png')
