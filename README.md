# VM Remote Reboot Server

这是一个简单的Python服务，用于监听特定端口并在接收到有效请求时重启Debian系统虚拟机。主要用于解决Vue项目编译时内存溢出导致虚拟机卡死的问题。

## 功能特点

- 监听本地20086端口，接收HTTP请求
- 验证请求中的安全令牌
- 记录请求日志（时间、来源IP）
- 执行系统重启命令
- 支持通过systemd设置开机自启

## 安装和使用

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd reboot_server
```

### 2. 配置服务

编辑`config.ini`文件，设置安全令牌和其他参数：

```ini
[Server]
port = 20086
host = 0.0.0.0

[Security]
token = your_secure_token_here_please_change_this

[Logging]
log_file = /var/log/reboot_server.log
log_level = INFO
```

**重要**：请务必修改默认的安全令牌，使用强密码。

### 3. 手动运行服务

```bash
sudo python3 reboot_server.py --config config.ini
```

### 4. 设置为系统服务（推荐）

```bash
# 复制服务文件到systemd目录
sudo cp reboot-server.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable reboot-server.service

# 启动服务
sudo systemctl start reboot-server.service

# 检查服务状态
sudo systemctl status reboot-server.service
```

## 触发重启

当虚拟机卡死时，可以通过以下方式触发重启：

```bash
curl http://[vm_ip]:20086/reboot?token=your_secure_token_here
```

或者在浏览器中访问：

```
http://[vm_ip]:20086/reboot?token=your_secure_token_here
```

## 查看日志

```bash
sudo tail -f /var/log/reboot_server.log
```

## 注意事项

1. 该服务需要以root权限运行才能执行系统重启命令
2. 请确保在生产环境中使用强安全令牌
3. 建议仅在内部网络中使用，或配合防火墙限制访问
4. 定期检查日志文件，确保服务正常运行

## 故障排除

如果服务无法启动或无法正常工作，请检查：

1. 服务是否以root权限运行
2. 配置文件中的端口是否被其他程序占用
3. 防火墙是否允许该端口的访问
4. 查看日志文件获取详细错误信息