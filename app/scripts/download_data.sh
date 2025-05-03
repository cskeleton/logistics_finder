#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"  # 只上移一层
DATA_DIR="$PROJECT_ROOT/data"
DB_FILE="$DATA_DIR/china.db"
TEMP_DB_FILE="$DATA_DIR/china.db.tmp"

# 检查当前的DB_FILE路径
echo "Current DB_FILE path is: ' $DB_FILE ' ."

# 创建数据目录（如果不存在）
mkdir -p "$DATA_DIR"

# 检查数据库文件是否存在且不为空
if [ -f "$DB_FILE" ] && [ -s "$DB_FILE" ]; then
    # 验证现有数据库文件是否有效
    if sqlite3 "$DB_FILE" "SELECT 1;" >/dev/null 2>&1; then
        echo "行政区划数据库文件已存在且有效，跳过下载。"
        exit 0
    else
        echo "警告：现有行政区划数据库文件可能已损坏，将重新下载..."
        rm -f "$DB_FILE"
    fi
fi

echo "开始下载行政区划数据库文件..."
# 下载到临时文件
if curl -L "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/refs/heads/master/dist/data.sqlite" -o "$TEMP_DB_FILE"; then
    # 检查临时文件是否成功下载且不为空
    if [ -s "$TEMP_DB_FILE" ]; then
        # 验证下载的文件是否为有效的SQLite数据库
        if sqlite3 "$TEMP_DB_FILE" "SELECT 1;" >/dev/null 2>&1; then
            # 移动临时文件到目标位置
            mv "$TEMP_DB_FILE" "$DB_FILE"
            # 设置适当的权限
            chmod 644 "$DB_FILE"
            echo "下载完成！行政区划数据库文件验证成功。"
        else
            echo "错误：下载的行政区划数据库文件不是有效的SQLite数据库"
            rm -f "$TEMP_DB_FILE"
            exit 1
        fi
    else
        echo "错误：下载的行政区划数据库文件为空"
        rm -f "$TEMP_DB_FILE"
        exit 1
    fi
else
    echo "错误：下载行政区划数据库文件失败"
    rm -f "$TEMP_DB_FILE"
    exit 1
fi 