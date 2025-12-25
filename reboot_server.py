#!/usr/bin/env python3
"""
虚拟机远程重启服务
用于监听特定端口，接收重启请求并执行系统重启命令
"""

import http.server
import socketserver
import subprocess
import logging
import argparse
import configparser
import os
import time
from urllib.parse import urlparse, parse_qs


class RebootHandler(http.server.BaseHTTPRequestHandler):
    """处理重启请求的HTTP处理器"""
    
    # 配置和日志记录器将在初始化时设置
    config = None
    logger = None
    
    @classmethod
    def initialize(cls, config, logger):
        """初始化处理器的配置和日志记录器"""
        cls.config = config
        cls.logger = logger
    
    def do_GET(self):
        """处理GET请求"""
        # 解析URL和查询参数
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # 检查请求路径是否为重启路径
        if parsed_url.path == '/reboot':
            # 验证令牌
            token = query_params.get('token', [None])[0]
            expected_token = self.config.get('Security', 'token')
            
            if not token:
                self._send_error(400, "Missing token parameter")
                self.logger.warning(f"Missing token from {self.client_address[0]}")
                return
            
            if token != expected_token:
                self._send_error(401, "Invalid token")
                self.logger.warning(f"Invalid token from {self.client_address[0]}")
                return
            
            # 记录有效的重启请求
            self.logger.info(f"Reboot request received from {self.client_address[0]}")
            
            # 发送确认响应
            self._send_response("Reboot command received, system will restart shortly")
            
            # 在后台执行重启命令
            self._execute_reboot()
        else:
            self._send_error(404, "Not Found")
    
    def _send_response(self, message):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    def _send_error(self, code, message):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    def _execute_reboot(self):
        """在后台执行系统重启命令"""
        try:
            # 使用subprocess在后台执行重启命令
            # 添加5秒延迟，确保响应能够发送完成
            subprocess.Popen(['sh', '-c', 'sleep 5 && /sbin/shutdown -r now'], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
            self.logger.info("Reboot command executed")
        except Exception as e:
            self.logger.error(f"Failed to execute reboot command: {str(e)}")
    
    def log_message(self, format, *args):
        """覆盖日志方法，使用我们自己的日志记录器"""
        self.logger.info(f"{self.client_address[0]} - {format % args}")


def setup_logging(config):
    """设置日志记录"""
    log_file = config.get('Logging', 'log_file', fallback='reboot_server.log')
    log_level = config.get('Logging', 'log_level', fallback='INFO')
    
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志记录器
    logger = logging.getLogger('reboot_server')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def load_config(config_file):
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    # 如果配置文件存在，加载它
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        # 创建默认配置
        config['Server'] = {
            'port': '20086',
            'host': '0.0.0.0'
        }
        config['Security'] = {
            'token': 'default_secure_token_change_me'
        }
        config['Logging'] = {
            'log_file': 'reboot_server.log',
            'log_level': 'INFO'
        }
        
        # 保存默认配置
        with open(config_file, 'w') as f:
            config.write(f)
    
    return config


def run_server(config, logger):
    """运行HTTP服务器"""
    host = config.get('Server', 'host', fallback='0.0.0.0')
    port = int(config.get('Server', 'port', fallback='20086'))
    
    # 设置处理器的配置和日志记录器
    RebootHandler.initialize(config, logger)
    
    # 创建服务器
    with socketserver.TCPServer((host, port), RebootHandler) as httpd:
        logger.info(f"Server started at http://{host}:{port}")
        logger.info("To reboot the system, send a GET request to /reboot?token=YOUR_TOKEN")
        
        try:
            # 运行服务器直到被中断
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by keyboard interrupt")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            httpd.server_close()
            logger.info("Server stopped")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='VM Remote Reboot Server')
    parser.add_argument('--config', default='config.ini', help='Path to configuration file')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置日志记录
    logger = setup_logging(config)
    
    # 检查是否以root权限运行
    if os.geteuid() != 0:
        logger.warning("This script should be run as root to execute reboot commands")
    
    # 运行服务器
    run_server(config, logger)


if __name__ == '__main__':
    main()