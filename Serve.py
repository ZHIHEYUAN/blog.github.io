import http.server
import socketserver
import time
import os

# 定义限速类
class ThrottledHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    # 限速参数，单位：字节/秒
    RATE_LIMIT = 1 * 1024
    # 访问间隔时间，单位：秒（禁止访问 1 分钟）
    ACCESS_BLOCK_TIME = 2
    # 记录每个用户的上次访问时间
    client_last_access = {}

    def send(self, data):
        # 计算发送数据所需的时间
        time_to_send = len(data) / self.RATE_LIMIT
        start_time = time.time()
        # 发送数据
        self.wfile.write(data)
        # 计算已经过去的时间
        elapsed_time = time.time() - start_time
        if elapsed_time < time_to_send:
            # 如果发送时间小于所需时间，进行休眠
            time.sleep(time_to_send - elapsed_time)

    def do_GET(self):
        client_address = self.client_address[0]  # 获取客户端IP地址
        current_time = time.time()

        # 检查用户是否在禁止访问时间内
        if client_address in self.client_last_access:
            last_access_time = self.client_last_access[client_address]
            if current_time - last_access_time < self.ACCESS_BLOCK_TIME:
                # 如果在禁止访问时间内，返回 429 错误（太多请求）
                self.send_error(429, 'Too Many Requests. Try again later.')
                return

        # 更新用户的上次访问时间
        self.client_last_access[client_address] = current_time

        if self.path == '/':
            self.path = '/index.html'
        try:
            # 尝试打开请求的文件
            file_path = '.' + self.path
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as file:
                    content = file.read()
                # 设置响应状态码为 200
                self.send_response(200)
                # 根据文件扩展名设置 Content-Type
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                self.end_headers()
                # 按块发送数据并进行限速
                chunk_size = self.RATE_LIMIT
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    self.send(chunk)
            else:
                # 如果文件不存在，尝试重定向到 404.html
                error_file_path = './404.html'
                if os.path.isfile(error_file_path):
                    with open(error_file_path, 'rb') as error_file:
                        error_content = error_file.read()
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    # 按块发送数据并进行限速
                    chunk_size = self.RATE_LIMIT
                    for i in range(0, len(error_content), chunk_size):
                        chunk = error_content[i:i + chunk_size]
                        self.send(chunk)
                else:
                    # 如果 404.html 也不存在，返回 404 错误
                    self.send_error(404, 'File Not Found: %s' % self.path)
        except Exception as e:
            # 发生其他错误时，返回 500 错误
            self.send_error(500, 'Internal Server Error: %s' % str(e))


# 定义服务器的端口
PORT = 80
# 监听地址设置为 0.0.0.0
HOST = '0.0.0.0'

# 创建一个 TCP 套接字服务器，使用自定义的请求处理程序
with socketserver.TCPServer((HOST, PORT), ThrottledHTTPRequestHandler) as httpd:
    print(f"Serving at {HOST}:{PORT} with a rate limit of {ThrottledHTTPRequestHandler.RATE_LIMIT} bytes per second.")
    try:
        # 启动服务器，开始监听请求
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user.")