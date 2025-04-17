#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 获取项目根目录
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
# 设置数据目录
DATA_DIR="$PROJECT_ROOT/app/data"
DB_FILE="$DATA_DIR/china.db"

# 创建数据目录（如果不存在）
mkdir -p "$DATA_DIR"

# 检查数据库文件是否存在
if [ ! -f "$DB_FILE" ]; then
    echo "数据库文件不存在，开始下载..."
    # 下载行政区划数据
    curl -L "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/refs/heads/master/dist/data.sqlite" -o "$DB_FILE"
    # 设置适当的权限
    chmod 644 "$DB_FILE"
    echo "下载完成！"
else
    echo "数据库文件已存在，跳过下载。"
fi 