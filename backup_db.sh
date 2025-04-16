#!/bin/bash

# --- 配置 ---
# Docker Compose 文件所在的目录 (你的应用部署目录)
APP_DIR="/home/your_deploy_user/expressfee"
# 数据库文件在容器内的路径 (相对于挂载的 volume)
DB_NAME="your_database_name.db" # <<< 修改为你实际的数据库文件名
# VPS 上挂载的 data 目录路径
DATA_DIR="${APP_DIR}/data"
# 数据库文件的完整路径
DB_FILE="${DATA_DIR}/${DB_NAME}"
# 备份文件存放目录 (建议放在部署目录之外)
BACKUP_DIR="/home/your_deploy_user/db_backups"
# 备份文件名前缀
BACKUP_PREFIX="expressfee_backup"
# 保留多少天的备份
RETENTION_DAYS=7
# --- 配置结束 ---

# 创建备份目录 (如果不存在)
mkdir -p "${BACKUP_DIR}"

# 生成带时间戳的备份文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="${BACKUP_PREFIX}_${TIMESTAMP}.db"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

echo "Starting database backup..."

# 检查数据库文件是否存在
if [ ! -f "${DB_FILE}" ]; then
  echo "Error: Database file ${DB_FILE} not found!"
  exit 1
fi

# 使用 sqlite3 的 .backup 命令创建一致性备份
# 这是比直接 cp 更安全的方式，因为它能处理正在写入的数据库
echo "Creating backup file: ${BACKUP_PATH}"
sqlite3 "${DB_FILE}" ".backup '${BACKUP_PATH}'"

# 检查备份是否成功
if [ $? -eq 0 ]; then
  echo "Database backup successful: ${BACKUP_PATH}"
else
  echo "Error: Database backup failed!"
  exit 1
fi

# (可选) 压缩备份文件
echo "Compressing backup file..."
gzip "${BACKUP_PATH}"
if [ $? -eq 0 ]; then
  echo "Backup file compressed: ${BACKUP_PATH}.gz"
else
  echo "Warning: Compression failed for ${BACKUP_PATH}"
fi

# (可选) 删除旧备份
echo "Deleting backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}*.gz" -type f -mtime +${RETENTION_DAYS} -exec echo "Deleting old backup: {}" \; -exec rm {} \;

echo "Backup process finished."
exit 0