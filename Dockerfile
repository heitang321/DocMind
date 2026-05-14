FROM python:3.11-slim

WORKDIR /app

# 替换 apt 源为清华 TUNA
# 注意：python:3.11-slim 当前已基于 Debian 13 Trixie，需匹配正确的发行版代号
RUN rm -rf /etc/apt/sources.list.d/*.sources && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ trixie-security main non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码（local_model 一并复制，未被 .dockerignore 排除）
COPY . .

# 创建运行时目录
RUN mkdir -p uploads faiss_indexes

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]