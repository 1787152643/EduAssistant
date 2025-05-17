from app import create_app

app = create_app()  # 调用工厂函数创建应用实例

if __name__ == "__main__":
    app.run()       # 可选，保留开发模式兼容性
