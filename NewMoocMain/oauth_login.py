#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth登录处理器
用于处理基于重定向的登录流程
"""

import socket
import threading
import webbrowser
import time
import random
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from MoocMain.log import Logger

logger = Logger(__name__).get_log()

class OAuthLoginHandler:
    """OAuth登录处理器"""
    
    def __init__(self, port=None):
        self.port = port
        self.token = None
        self.server = None
        self.server_thread = None
        self.is_running = False
        
    def find_available_port(self, preferred_port=None, max_attempts=50):
        """
        找到一个可用的端口
        
        Args:
            preferred_port: 首选端口，如果为None则随机选择
            max_attempts: 最大尝试次数
            
        Returns:
            可用的端口号
        """
        attempted_ports = set()
        
        # 如果有首选端口，先尝试
        if preferred_port and preferred_port not in attempted_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', preferred_port))
                    logger.debug(f"✅ 首选端口 {preferred_port} 可用")
                    return preferred_port
            except OSError:
                logger.debug(f"⚠️ 首选端口 {preferred_port} 被占用")
                attempted_ports.add(preferred_port)
        
        # 随机尝试端口
        for attempt in range(max_attempts):
            # 使用随机端口范围：30000-65535（避免系统保留端口）
            port = random.randint(30000, 65535)
            
            # 跳过已尝试过的端口
            if port in attempted_ports:
                continue
            
            attempted_ports.add(port)
            
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    logger.debug(f"✅ 随机端口 {port} 可用 (尝试第{attempt + 1}次)")
                    return port
            except OSError:
                logger.debug(f"⚠️ 端口 {port} 被占用")
                continue
        
        # 如果随机尝试失败，尝试常用端口范围
        logger.debug("🔄 随机端口尝试失败，尝试常用端口范围...")
        common_ports = list(range(39001, 39050)) + list(range(38000, 38050)) + list(range(37000, 37050))
        random.shuffle(common_ports)  # 随机打乱顺序
        
        for port in common_ports:
            if port in attempted_ports:
                continue
                
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    logger.debug(f"✅ 常用端口 {port} 可用")
                    return port
            except OSError:
                continue
        
        raise Exception(f"❌ 无法找到可用端口 (已尝试 {len(attempted_ports)} 个端口)")
    
    def create_request_handler(self):
        """创建HTTP请求处理器"""
        oauth_handler = self
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # 解析URL
                parsed_url = urlparse(self.path)
                
                if parsed_url.path == '/' or parsed_url.path == '':
                    # 首页 - 显示OAuth登录引导页面
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    welcome_html = """
                    <!DOCTYPE html>
                    <html lang="zh-CN">
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>OAuth登录服务 - MOOC助手</title>
                        <style>
                            * {
                                margin: 0;
                                padding: 0;
                                box-sizing: border-box;
                            }
                            
                            body {
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                min-height: 100vh;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                padding: 20px;
                            }
                            
                            .container {
                                background: white;
                                border-radius: 20px;
                                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                                padding: 40px;
                                text-align: center;
                                max-width: 500px;
                                width: 100%;
                                position: relative;
                                overflow: hidden;
                            }
                            
                            .container::before {
                                content: '';
                                position: absolute;
                                top: 0;
                                left: 0;
                                right: 0;
                                height: 4px;
                                background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
                                animation: gradient 3s ease infinite;
                            }
                            
                            @keyframes gradient {
                                0%, 100% { background-position: 0% 50%; }
                                50% { background-position: 100% 50%; }
                            }
                            
                            .logo {
                                font-size: 64px;
                                margin-bottom: 20px;
                                animation: pulse 2s ease-in-out infinite;
                            }
                            
                            @keyframes pulse {
                                0%, 100% { transform: scale(1); }
                                50% { transform: scale(1.05); }
                            }
                            
                            .title {
                                color: #667eea;
                                font-size: 28px;
                                font-weight: 600;
                                margin-bottom: 15px;
                            }
                            
                            .subtitle {
                                color: #6c757d;
                                font-size: 16px;
                                margin-bottom: 30px;
                                line-height: 1.6;
                            }
                            
                            .status {
                                background: #e8f5e8;
                                border: 2px solid #d4edda;
                                border-radius: 12px;
                                padding: 20px;
                                margin: 25px 0;
                            }
                            
                            .status-title {
                                color: #28a745;
                                font-weight: 600;
                                margin-bottom: 10px;
                                font-size: 18px;
                            }
                            
                            .status-message {
                                color: #155724;
                                font-size: 14px;
                                line-height: 1.6;
                            }
                            
                            .waiting {
                                margin-top: 30px;
                                color: #6c757d;
                                font-size: 14px;
                            }
                            
                            .spinner {
                                display: inline-block;
                                width: 20px;
                                height: 20px;
                                border: 3px solid #f3f3f3;
                                border-top: 3px solid #667eea;
                                border-radius: 50%;
                                animation: spin 1s linear infinite;
                                margin-right: 10px;
                            }
                            
                            @keyframes spin {
                                0% { transform: rotate(0deg); }
                                100% { transform: rotate(360deg); }
                            }
                            
                            .footer {
                                margin-top: 30px;
                                padding-top: 20px;
                                border-top: 1px solid #e9ecef;
                                color: #6c757d;
                                font-size: 12px;
                            }
                            
                            @media (max-width: 480px) {
                                .container {
                                    padding: 30px 20px;
                                }
                                
                                .logo {
                                    font-size: 48px;
                                }
                                
                                .title {
                                    font-size: 24px;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="logo">🚀</div>
                            <h1 class="title">OAuth登录服务</h1>
                            <p class="subtitle">
                                MOOC助手安全登录服务已启动<br>
                                正在等待您的登录授权...
                            </p>
                            
                            <div class="status">
                                <div class="status-title">✅ 服务状态：正常运行</div>
                                <div class="status-message">
                                    • 本地服务器已启动<br>
                                    • 正在监听登录回调<br>
                                    • 浏览器登录页面已打开
                                </div>
                            </div>
                            
                            <div class="waiting">
                                <div class="spinner"></div>
                                请在浏览器中完成登录流程...
                            </div>
                            
                            <div class="footer">
                                <div>🚀 MOOC助手 - 让学习更高效</div>
                                <div>🔐 安全登录 · 隐私保护</div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(welcome_html.encode('utf-8'))
                    
                elif parsed_url.path == '/login':
                    # 解析查询参数
                    query_params = parse_qs(parsed_url.query)
                    
                    if 'token' in query_params:
                        token = query_params['token'][0]
                        oauth_handler.token = token
                        logger.debug(f"✅ 回调成功，token: {token}")
                        
                        # 发送成功响应
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        
                        success_html = f"""
                        <!DOCTYPE html>
                        <html lang="zh-CN">
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>登录成功 - MOOC助手</title>
                            <style>
                                * {{
                                    margin: 0;
                                    padding: 0;
                                    box-sizing: border-box;
                                }}
                                
                                body {{
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    min-height: 100vh;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    padding: 20px;
                                }}
                                
                                .container {{
                                    background: white;
                                    border-radius: 20px;
                                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                                    padding: 40px;
                                    text-align: center;
                                    max-width: 500px;
                                    width: 100%;
                                    position: relative;
                                    overflow: hidden;
                                }}
                                
                                .container::before {{
                                    content: '';
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    right: 0;
                                    height: 4px;
                                    background: linear-gradient(90deg, #28a745, #20c997, #17a2b8);
                                }}
                                
                                .success-icon {{
                                    font-size: 64px;
                                    margin-bottom: 20px;
                                    animation: bounce 1s ease-in-out;
                                }}
                                
                                @keyframes bounce {{
                                    0%, 100% {{ transform: translateY(0); }}
                                    50% {{ transform: translateY(-10px); }}
                                }}
                                
                                .success-title {{
                                    color: #28a745;
                                    font-size: 28px;
                                    font-weight: 600;
                                    margin-bottom: 15px;
                                }}
                                
                                .success-message {{
                                    color: #6c757d;
                                    font-size: 16px;
                                    margin-bottom: 30px;
                                    line-height: 1.6;
                                }}
                                
                                .token-container {{
                                    background: #f8f9fa;
                                    border: 2px solid #e9ecef;
                                    border-radius: 12px;
                                    padding: 20px;
                                    margin: 25px 0;
                                    position: relative;
                                    overflow: hidden;
                                }}
                                
                                .token-label {{
                                    font-weight: 600;
                                    color: #495057;
                                    margin-bottom: 10px;
                                    font-size: 14px;
                                    text-transform: uppercase;
                                    letter-spacing: 0.5px;
                                }}
                                
                                .token-value {{
                                    font-family: 'Courier New', monospace;
                                    font-size: 14px;
                                    color: #007bff;
                                    word-break: break-all;
                                    background: white;
                                    padding: 15px;
                                    border-radius: 8px;
                                    border: 1px solid #dee2e6;
                                    position: relative;
                                }}
                                
                                .copy-btn {{
                                    position: absolute;
                                    top: 10px;
                                    right: 10px;
                                    background: #007bff;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    padding: 5px 10px;
                                    font-size: 12px;
                                    cursor: pointer;
                                    transition: background 0.3s;
                                }}
                                
                                .copy-btn:hover {{
                                    background: #0056b3;
                                }}
                                
                                .actions {{
                                    margin-top: 30px;
                                    display: flex;
                                    gap: 15px;
                                    justify-content: center;
                                    flex-wrap: wrap;
                                }}
                                
                                .btn {{
                                    padding: 12px 24px;
                                    border: none;
                                    border-radius: 8px;
                                    font-size: 16px;
                                    font-weight: 500;
                                    cursor: pointer;
                                    transition: all 0.3s;
                                    text-decoration: none;
                                    display: inline-block;
                                    min-width: 120px;
                                }}
                                
                                .btn-primary {{
                                    background: #007bff;
                                    color: white;
                                }}
                                
                                .btn-primary:hover {{
                                    background: #0056b3;
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 12px rgba(0,123,255,0.3);
                                }}
                                
                                .btn-secondary {{
                                    background: #6c757d;
                                    color: white;
                                }}
                                
                                .btn-secondary:hover {{
                                    background: #545b62;
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 12px rgba(108,117,125,0.3);
                                }}
                                
                                .countdown {{
                                    margin-top: 20px;
                                    font-size: 14px;
                                    color: #6c757d;
                                }}
                                
                                .countdown-number {{
                                    font-weight: 600;
                                    color: #007bff;
                                }}
                                
                                .footer {{
                                    margin-top: 30px;
                                    padding-top: 20px;
                                    border-top: 1px solid #e9ecef;
                                    color: #6c757d;
                                    font-size: 12px;
                                }}
                                
                                @media (max-width: 480px) {{
                                    .container {{
                                        padding: 30px 20px;
                                    }}
                                    
                                    .success-icon {{
                                        font-size: 48px;
                                    }}
                                    
                                    .success-title {{
                                        font-size: 24px;
                                    }}
                                    
                                    .actions {{
                                        flex-direction: column;
                                    }}
                                    
                                    .btn {{
                                        width: 100%;
                                    }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="success-icon">🎉</div>
                                <h1 class="success-title">登录成功</h1>
                                <p class="success-message">
                                    恭喜！您已成功通过OAuth认证登录。<br>
                                    Token已安全获取，请返回应用程序继续操作。
                                </p>
                                
                                <div class="token-container">
                                    <div class="token-label">🔐 认证令牌</div>
                                    <div class="token-value" id="tokenValue">
                                        {token}
                                        <button class="copy-btn" onclick="copyToken()">复制</button>
                                    </div>
                                </div>
                                
                                <div class="actions">
                                    <button class="btn btn-primary" onclick="window.close()">关闭页面</button>
                                    <button class="btn btn-secondary" onclick="copyToken()">复制Token</button>
                                </div>
                                
                                <div class="countdown">
                                    页面将在 <span class="countdown-number" id="countdown">5</span> 秒后自动关闭
                                </div>
                                
                                <div class="footer">
                                    <div>🚀 MOOC助手 - 让学习更高效</div>
                                    <div>✨ 安全登录 · 智能助手 · 开源免费</div>
                                </div>
                            </div>
                            
                            <script>
                                let countdown = 5;
                                const countdownElement = document.getElementById('countdown');
                                
                                function updateCountdown() {{
                                    countdown--;
                                    if (countdownElement) {{
                                        countdownElement.textContent = countdown;
                                    }}
                                    
                                    if (countdown <= 0) {{
                                        window.close();
                                    }} else {{
                                        setTimeout(updateCountdown, 1000);
                                    }}
                                }}
                                
                                function copyToken() {{
                                    const token = '{token}';
                                    if (navigator.clipboard) {{
                                        navigator.clipboard.writeText(token).then(() => {{
                                            const btn = document.querySelector('.copy-btn');
                                            const originalText = btn.textContent;
                                            btn.textContent = '已复制';
                                            btn.style.background = '#28a745';
                                            setTimeout(() => {{
                                                btn.textContent = originalText;
                                                btn.style.background = '#007bff';
                                            }}, 2000);
                                        }});
                                    }} else {{
                                        // 兼容旧浏览器
                                        const textArea = document.createElement('textarea');
                                        textArea.value = token;
                                        document.body.appendChild(textArea);
                                        textArea.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(textArea);
                                        
                                        const btn = document.querySelector('.copy-btn');
                                        btn.textContent = '已复制';
                                        btn.style.background = '#28a745';
                                        setTimeout(() => {{
                                            btn.textContent = '复制';
                                            btn.style.background = '#007bff';
                                        }}, 2000);
                                    }}
                                }}
                                
                                // 启动倒计时
                                setTimeout(updateCountdown, 1000);
                            </script>
                        </body>
                        </html>
                        """
                        
                        self.wfile.write(success_html.encode('utf-8'))
                        
                        # 延迟关闭服务器
                        threading.Timer(2.0, oauth_handler.stop_server).start()
                        
                    else:
                        # 没有token参数
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        
                        error_html = """
                        <!DOCTYPE html>
                        <html lang="zh-CN">
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>登录失败 - MOOC助手</title>
                            <style>
                                * {
                                    margin: 0;
                                    padding: 0;
                                    box-sizing: border-box;
                                }
                                
                                body {
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                                    min-height: 100vh;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    padding: 20px;
                                }
                                
                                .container {
                                    background: white;
                                    border-radius: 20px;
                                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                                    padding: 40px;
                                    text-align: center;
                                    max-width: 500px;
                                    width: 100%;
                                    position: relative;
                                    overflow: hidden;
                                }
                                
                                .container::before {
                                    content: '';
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    right: 0;
                                    height: 4px;
                                    background: linear-gradient(90deg, #dc3545, #e74c3c, #c0392b);
                                }
                                
                                .error-icon {
                                    font-size: 64px;
                                    margin-bottom: 20px;
                                    animation: shake 0.5s ease-in-out;
                                }
                                
                                @keyframes shake {
                                    0%, 100% { transform: translateX(0); }
                                    25% { transform: translateX(-5px); }
                                    75% { transform: translateX(5px); }
                                }
                                
                                .error-title {
                                    color: #dc3545;
                                    font-size: 28px;
                                    font-weight: 600;
                                    margin-bottom: 15px;
                                }
                                
                                .error-message {
                                    color: #6c757d;
                                    font-size: 16px;
                                    margin-bottom: 30px;
                                    line-height: 1.6;
                                }
                                
                                .actions {
                                    margin-top: 30px;
                                    display: flex;
                                    gap: 15px;
                                    justify-content: center;
                                    flex-wrap: wrap;
                                }
                                
                                .btn {
                                    padding: 12px 24px;
                                    border: none;
                                    border-radius: 8px;
                                    font-size: 16px;
                                    font-weight: 500;
                                    cursor: pointer;
                                    transition: all 0.3s;
                                    text-decoration: none;
                                    display: inline-block;
                                    min-width: 120px;
                                }
                                
                                .btn-danger {
                                    background: #dc3545;
                                    color: white;
                                }
                                
                                .btn-danger:hover {
                                    background: #c82333;
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 12px rgba(220,53,69,0.3);
                                }
                                
                                .btn-secondary {
                                    background: #6c757d;
                                    color: white;
                                }
                                
                                .btn-secondary:hover {
                                    background: #545b62;
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 12px rgba(108,117,125,0.3);
                                }
                                
                                .help-section {
                                    margin-top: 30px;
                                    padding: 20px;
                                    background: #f8f9fa;
                                    border-radius: 12px;
                                    border-left: 4px solid #ffc107;
                                }
                                
                                .help-title {
                                    font-weight: 600;
                                    color: #495057;
                                    margin-bottom: 10px;
                                    font-size: 16px;
                                }
                                
                                .help-list {
                                    text-align: left;
                                    color: #6c757d;
                                    font-size: 14px;
                                    line-height: 1.8;
                                }
                                
                                .help-list li {
                                    margin-bottom: 8px;
                                }
                                
                                .footer {
                                    margin-top: 30px;
                                    padding-top: 20px;
                                    border-top: 1px solid #e9ecef;
                                    color: #6c757d;
                                    font-size: 12px;
                                }
                                
                                @media (max-width: 480px) {
                                    .container {
                                        padding: 30px 20px;
                                    }
                                    
                                    .error-icon {
                                        font-size: 48px;
                                    }
                                    
                                    .error-title {
                                        font-size: 24px;
                                    }
                                    
                                    .actions {
                                        flex-direction: column;
                                    }
                                    
                                    .btn {
                                        width: 100%;
                                    }
                                }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="error-icon">😞</div>
                                <h1 class="error-title">登录失败</h1>
                                <p class="error-message">
                                    很抱歉，未能获取到有效的认证令牌。<br>
                                    请检查登录流程并重试。
                                </p>
                                
                                <div class="help-section">
                                    <div class="help-title">⚡ 可能的解决方案</div>
                                    <ul class="help-list">
                                        <li>确保在浏览器中完成了完整的登录流程</li>
                                        <li>检查网络连接是否正常</li>
                                        <li>尝试刷新页面重新登录</li>
                                        <li>清除浏览器缓存和Cookie</li>
                                        <li>使用其他浏览器或无痕模式</li>
                                    </ul>
                                </div>
                                
                                <div class="actions">
                                    <button class="btn btn-danger" onclick="window.close()">关闭页面</button>
                                    <button class="btn btn-secondary" onclick="window.location.reload()">重新刷新</button>
                                </div>
                                
                                <div class="footer">
                                    <div>🚀 MOOC助手 - 让学习更高效</div>
                                    <div>❓ 如有问题请联系技术支持</div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        self.wfile.write(error_html.encode('utf-8'))
                        
                else:
                    # 其他路径返回404
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    not_found_html = """
                    <!DOCTYPE html>
                    <html lang="zh-CN">
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>页面未找到 - MOOC助手</title>
                        <style>
                            * {
                                margin: 0;
                                padding: 0;
                                box-sizing: border-box;
                            }
                            
                            body {
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                                min-height: 100vh;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                padding: 20px;
                            }
                            
                            .container {
                                background: white;
                                border-radius: 20px;
                                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                                padding: 40px;
                                text-align: center;
                                max-width: 500px;
                                width: 100%;
                                position: relative;
                                overflow: hidden;
                            }
                            
                            .container::before {
                                content: '';
                                position: absolute;
                                top: 0;
                                left: 0;
                                right: 0;
                                height: 4px;
                                background: linear-gradient(90deg, #fd79a8, #e84393, #a29bfe);
                            }
                            
                            .not-found-icon {
                                font-size: 64px;
                                margin-bottom: 20px;
                                animation: float 2s ease-in-out infinite;
                            }
                            
                            @keyframes float {
                                0%, 100% { transform: translateY(0px); }
                                50% { transform: translateY(-10px); }
                            }
                            
                            .not-found-title {
                                color: #6c5ce7;
                                font-size: 28px;
                                font-weight: 600;
                                margin-bottom: 15px;
                            }
                            
                            .not-found-message {
                                color: #6c757d;
                                font-size: 16px;
                                margin-bottom: 30px;
                                line-height: 1.6;
                            }
                            
                            .info-section {
                                margin-top: 30px;
                                padding: 20px;
                                background: #f8f9fa;
                                border-radius: 12px;
                                border-left: 4px solid #17a2b8;
                            }
                            
                            .info-title {
                                font-weight: 600;
                                color: #495057;
                                margin-bottom: 10px;
                                font-size: 16px;
                            }
                            
                            .info-text {
                                color: #6c757d;
                                font-size: 14px;
                                line-height: 1.8;
                            }
                            
                            .actions {
                                margin-top: 30px;
                                display: flex;
                                gap: 15px;
                                justify-content: center;
                                flex-wrap: wrap;
                            }
                            
                            .btn {
                                padding: 12px 24px;
                                border: none;
                                border-radius: 8px;
                                font-size: 16px;
                                font-weight: 500;
                                cursor: pointer;
                                transition: all 0.3s;
                                text-decoration: none;
                                display: inline-block;
                                min-width: 120px;
                            }
                            
                            .btn-info {
                                background: #17a2b8;
                                color: white;
                            }
                            
                            .btn-info:hover {
                                background: #138496;
                                transform: translateY(-2px);
                                box-shadow: 0 4px 12px rgba(23,162,184,0.3);
                            }
                            
                            .btn-secondary {
                                background: #6c757d;
                                color: white;
                            }
                            
                            .btn-secondary:hover {
                                background: #545b62;
                                transform: translateY(-2px);
                                box-shadow: 0 4px 12px rgba(108,117,125,0.3);
                            }
                            
                            .footer {
                                margin-top: 30px;
                                padding-top: 20px;
                                border-top: 1px solid #e9ecef;
                                color: #6c757d;
                                font-size: 12px;
                            }
                            
                            @media (max-width: 480px) {
                                .container {
                                    padding: 30px 20px;
                                }
                                
                                .not-found-icon {
                                    font-size: 48px;
                                }
                                
                                .not-found-title {
                                    font-size: 24px;
                                }
                                
                                .actions {
                                    flex-direction: column;
                                }
                                
                                .btn {
                                    width: 100%;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="not-found-icon">🔍</div>
                            <h1 class="not-found-title">页面未找到</h1>
                            <p class="not-found-message">
                                抱歉，您访问的页面不存在。<br>
                                请检查URL地址是否正确。
                            </p>
                            
                            <div class="info-section">
                                <div class="info-title">💡 温馨提示</div>
                                <div class="info-text">
                                    OAuth登录回调页面地址应为：<br>
                                    <strong>/login?token=您的令牌</strong>
                                </div>
                            </div>
                            
                            <div class="actions">
                                <button class="btn btn-info" onclick="window.close()">关闭页面</button>
                                <button class="btn btn-secondary" onclick="window.history.back()">返回上页</button>
                            </div>
                            
                            <div class="footer">
                                <div>🚀 MOOC助手 - 让学习更高效</div>
                                <div>🔗 OAuth登录服务</div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(not_found_html.encode('utf-8'))
            
            def log_message(self, format, *args):
                # 禁用默认日志输出
                pass
        
        return RequestHandler
    
    def start_server(self, retry_count=3):
        """
        启动HTTP服务器
        
        Args:
            retry_count: 重试次数
            
        Returns:
            成功返回True，失败返回False
        """
        for attempt in range(retry_count):
            try:
                # 找到可用端口
                self.port = self.find_available_port(self.port)
                
                # 创建HTTP服务器
                self.server = HTTPServer(('', self.port), self.create_request_handler())
                self.is_running = True
                
                logger.info(f"🚀 OAuth服务已就绪，端口: {self.port}")
                logger.debug(f"   回调地址: http://localhost:{self.port}/login")
                logger.debug(f"   登录URL: https://sso.icve.com.cn/sso/auth?mode=simple&source=2&redirect=http://localhost:{self.port}/login")
                
                # 在新线程中运行服务器
                self.server_thread = threading.Thread(target=self.server.serve_forever)
                self.server_thread.daemon = True
                self.server_thread.start()
                
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ 启动OAuth登录服务器失败 (尝试第{attempt + 1}次): {e}")
                
                # 如果不是最后一次尝试，重置端口并重试
                if attempt < retry_count - 1:
                    self.port = None  # 重置端口，下次尝试时会重新随机选择
                    time.sleep(1)  # 稍等片刻再重试
                    continue
                else:
                    logger.error(f"❌ 启动OAuth登录服务器失败 (已重试{retry_count}次)")
                    return False
        
        return False
    
    def stop_server(self):
        """停止HTTP服务器"""
        if self.server and self.is_running:
            self.server.shutdown()
            self.server.server_close()
            self.is_running = False
            logger.info("🛑 OAuth登录服务器已停止")
    
    def open_login_page(self):
        """打开登录页面"""
        # 构建重定向URL
        redirect_url = f"http://localhost:{self.port}/login"
        login_url = f"https://sso.icve.com.cn/sso/auth?mode=simple&source=2&redirect={redirect_url}"
        
        logger.info(f"🌐 浏览器已打开，请完成登录...")
        
        try:
            webbrowser.open(login_url)
            return True
        except Exception as e:
            logger.error(f"❌ 无法打开浏览器: {e}")
            logger.info(f"请手动打开以下URL进行登录: {login_url}")
            return False
    
    def wait_for_token(self, timeout=300):
        """等待token获取"""
        start_time = time.time()
        while self.token is None and time.time() - start_time < timeout:
            if not self.is_running:
                break
            time.sleep(0.5)
        
        if self.token:
            return self.token
        else:
            logger.error("❌ 登录超时")
            return None
    
    def login(self, timeout=300):
        """
        执行OAuth登录流程
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            成功返回token字符串，失败返回None
        """
        try:
            # 1. 启动HTTP服务器
            if not self.start_server():
                return None
            
            # 2. 打开登录页面
            self.open_login_page()
            
            # 3. 等待token获取
            token = self.wait_for_token(timeout)
            
            # 4. 清理资源
            self.stop_server()
            
            return token
            
        except Exception as e:
            logger.error(f"❌ OAuth登录过程中发生异常: {e}")
            self.stop_server()
            return None
    
    def __del__(self):
        """析构函数，确保服务器被正确关闭"""
        self.stop_server()


def oauth_login(timeout=300, preferred_port=None):
    """
    OAuth登录的便捷函数
    
    Args:
        timeout: 超时时间（秒）
        preferred_port: 首选端口，如果为None则随机选择
        
    Returns:
        成功返回token字符串，失败返回None
    """
    handler = OAuthLoginHandler(port=preferred_port)
    return handler.login(timeout)


if __name__ == "__main__":
    # 测试OAuth登录
    print("🔐 测试OAuth登录流程")
    print("=" * 50)
    print("📝 说明：端口会随机选择，如果被占用会自动切换")
    print("🎲 端口范围：30000-65535（随机选择）")
    print("=" * 50)
    
    token = oauth_login()
    
    if token:
        print(f"✅ 登录成功！")
        print(f"🎯 Token: {token}")
    else:
        print("❌ 登录失败！") 