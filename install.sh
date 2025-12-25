#!/bin/bash
"""
安装脚本
用于设置和启动VM远程重启服务
"""

set -e

# 脚本必须以root权限运行
if [ "$(id -u)" != "0" ]; then
   echo "此脚本必须以root权限运行" 
   exit 1
fi

# 项目目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="reboot-server"
SERVICE_FILE="$PROJECT_DIR/$SERVICE_NAME.service"
CONFIG_FILE="$PROJECT_DIR/config.ini"

echo "===== VM远程重启服务安装脚本 ====="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3。请先安装Python3。"
    exit 1
fi

# 更新systemd服务文件中的路径
echo "更新systemd服务文件..."
sed -i "s|/home/user/vibecoding/workspace/reboot_server|$PROJECT_DIR|g" "$SERVICE_FILE"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件不存在。"
    exit 1
fi

# 提示用户修改安全令牌
echo ""
echo "请确保您已在配置文件中设置了强安全令牌。"
echo "当前配置文件中的令牌:"
grep -A 1 "\[Security\]" "$CONFIG_FILE" | tail -n 1
echo ""
read -p "是否继续安装？(y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "安装已取消。请先修改配置文件中的安全令牌。"
    exit 1
fi

# 创建日志目录
LOG_DIR=$(grep -A 1 "\[Logging\]" "$CONFIG_FILE" | grep log_file | cut -d '=' -f 2 | tr -d ' ' | xargs dirname)
if [ ! -d "$LOG_DIR" ]; then
    echo "创建日志目录: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# 复制服务文件到systemd目录
echo "安装systemd服务..."
cp "$SERVICE_FILE" /etc/systemd/system/

# 重新加载systemd配置
echo "重新加载systemd配置..."
systemctl daemon-reload

# 启用服务（开机自启）
echo "启用服务（开机自启）..."
systemctl enable "$SERVICE_NAME.service"

# 启动服务
echo "启动服务..."
systemctl start "$SERVICE_NAME.service"

# 检查服务状态
echo ""
echo "检查服务状态..."
systemctl status "$SERVICE_NAME.service" --no-pager

echo ""
echo "===== 安装完成 ====="
echo ""
echo "使用以下命令触发重启:"
echo "curl http://[vm_ip]:20086/reboot?token=YOUR_TOKEN"
echo ""
echo "查看日志:"
echo "tail -f $(grep -A 1 "\[Logging\]" "$CONFIG_FILE" | grep log_file | cut -d '=' -f 2 | tr -d ' ')"
echo ""