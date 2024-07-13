import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from markdown import markdown
from markupsafe import Markup
from mdbeamer.splitter import paginate

def md(text):
    return Markup(markdown(text))

# 设置 Jinja2 环境
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'default')
tmp_dir = os.path.join(os.path.dirname(__file__), "..", "tmp")  # 确保 tmp 目录存在
env = Environment(loader=FileSystemLoader(template_dir))

# 添加自定义过滤器
env.filters['markdown'] = md

# 加载基础模板
template = env.get_template('base.html')

# 准备要填充到模板中的数据
with open(os.path.join(tmp_dir, 'testdoc.md')) as f:
    document = f.read()
pages = paginate(document)

data = {
    "title": "My Awesome Presentation",
    "slides": [
        {
            "h1": page.h1,
            "h2": page.h2,
            "h3": page.h3,
            "contents": [c.content for c in page.chunks],
            "layout": page.option.layout,
        }
        for page in pages
    ],
}

# 渲染模板
output = template.render(data)

# 确保 tmp 目录存在
os.makedirs(tmp_dir, exist_ok=True)

# 将渲染后的 HTML 写入文件
output_file = os.path.join(tmp_dir, f'presentation.html')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Presentation has been generated and saved to: {output_file}")
