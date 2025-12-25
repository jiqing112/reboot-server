#!/bin/bash
"""
卸载脚本
用于停止和移除VM远程重启服务
"""

set -e

# 脚本必须以root权限运行
if [ "$(id -u)" != "0" ]; then
   echo "此脚本必须以root权限运行" 
   exit 1
fi

SERVICE_NAME="reboot-server"

echo "===== VM远程重启服务卸载脚本 ====="

# 检查服务是否存在
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "错误: 服务 $SERVICE_NAME.service 不存在。"
    exit 1
fi

# 停止服务
echo "停止服务..."
systemctl stop "$SERVICE_NAME.service"

# 禁用服务（取消开机自启）
echo "禁用服务（取消开机自启）..."
systemctl disable "$SERVICE_NAME.service"

# 删除服务文件
echo "删除服务文件..."
rm -f "/etc/systemd/system/$SERVICE_NAME.service"

# 重新加载systemd配置
echo "重新加载systemd配置..."
systemctl daemon-reload

echo ""
echo "===== 卸载完成 ====="
echo "服务已成功移除。"
echo "注意：项目文件仍然保留在原位置，您可以手动删除。"