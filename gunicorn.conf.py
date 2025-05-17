# gunicorn.conf.py
import multiprocessing

# 核心配置
workers = multiprocessing.cpu_count() * 2 + 1  # 4vCPU → 9 workers
worker_class = "gevent"                        # 协程模式
worker_connections = 1000                      # 单个Worker最大连接数
bind = "0.0.0.0:5000"                         # 监听地址
timeout = 30                                   # 请求超时时间（秒）
max_requests = 1000                            # 自动重启Worker防内存泄漏
keepalive = 5                                  # Keep-Alive短连接优化

# 日志配置（生产环境建议输出到文件）
accesslog = "-"  # 标准输出（如需文件，改为路径如 "/var/log/gunicorn/access.log"）
errorlog = "-"   # 标准输出（如需文件，改为路径如 "/var/log/gunicorn/error.log"）

# 安全限制（防止恶意大请求）
limit_request_line = 4094
limit_request_fields = 100

# 适配Flask工厂模式（关键！）
def post_worker_init(worker):
    from wsgi import app  # 从wsgi入口导入工厂创建的app实例
    worker.app = app      # 绑定到Worker
