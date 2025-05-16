import requests
import time

# Configuration
BASE_URL = "http://124.71.46.184:5000"
SESSION_TOKEN = "eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6InByb2ZfemhhbmcifQ.aCb3yQ.vQXu-mgJ1ICUB-yuVTDiw6fbcmU"

# Prepare session with cookies
session = requests.Session()
session.cookies.set("session", SESSION_TOKEN)

# List of knowledge entries to add
knowledge_entries = [
    {
        "title": "算法复杂度分析",
        "content": "算法复杂度分析是评估算法效率的重要方法。时间复杂度描述算法执行所需的时间随输入规模的增长关系，常用大O符号表示。常见的时间复杂度包括O(1)、O(log n)、O(n)、O(n log n)、O(n²)、O(2^n)等。空间复杂度描述算法所需额外空间随输入规模的增长关系。分析复杂度时，主要关注最坏情况和平均情况。",
        "course_id": "1",
        "category": "算法",
        "tags": "算法分析, 时间复杂度, 空间复杂度, 大O表示法"
    },
    {
        "title": "常见排序算法比较",
        "content": "排序算法是计算机科学中的基础算法。常见排序算法性能比较：1. 快速排序：平均O(n log n)，不稳定；2. 归并排序：O(n log n)，稳定；3. 堆排序：O(n log n)，不稳定；4. 插入排序：最坏O(n²)，适合小数据集，稳定；5. 冒泡排序：O(n²)，简单但低效，稳定；6. 计数排序：O(n+k)，适用于有限范围整数；7. 基数排序：O(d(n+k))，适用于固定长度的数据。",
        "course_id": "1",
        "category": "算法",
        "tags": "排序算法, 快速排序, 归并排序, 算法效率"
    },
    {
        "title": "数据结构设计原则",
        "content": "设计高效数据结构应考虑：1. 数据访问模式（随机访问vs顺序访问）；2. 操作频率（查询、插入、删除）；3. 内存使用和数据局部性；4. 并发安全性需求；5. 可扩展性。常见数据结构的选择依据：数组适合固定大小且需随机访问；链表适合频繁插入删除；哈希表适合O(1)查找；树结构适合有序数据和层次关系；图适合表示复杂关系网络。",
        "course_id": "1",
        "category": "数据结构",
        "tags": "数据结构, 设计原则, 性能优化, 数据组织"
    },
    {
        "title": "平衡树结构",
        "content": "平衡树是一类特殊的二叉搜索树，通过自平衡机制保持树的高度最小，优化查找效率。常见平衡树包括：1. AVL树：严格平衡，任意节点的左右子树高度差不超过1，插入删除需旋转操作；2. 红黑树：近似平衡，保证从根到叶子的最长路径不超过最短路径的两倍，广泛应用于标准库实现；3. B树和B+树：多路平衡树，适用于磁盘存储系统和数据库索引；4. 伸展树：根据访问频率自调整结构。",
        "course_id": "1",
        "category": "数据结构",
        "tags": "平衡树, AVL树, 红黑树, B树, 数据库索引"
    },
    {
        "title": "面向对象设计原则",
        "content": "SOLID原则是面向对象设计的五个基本原则：1. 单一责任原则(SRP)：一个类只负责一个功能领域；2. 开闭原则(OCP)：对扩展开放，对修改关闭；3. 里氏替换原则(LSP)：子类能够替换父类并且保持系统行为一致；4. 接口隔离原则(ISP)：客户端不应依赖它不需要的接口；5. 依赖倒置原则(DIP)：高层模块不应依赖低层模块，都应依赖抽象。遵循这些原则可以提高代码的可维护性、可扩展性和可重用性。",
        "course_id": "2",
        "category": "软件工程",
        "tags": "SOLID原则, 面向对象设计, 设计模式, 软件架构"
    },
    {
        "title": "设计模式分类与应用",
        "content": "设计模式是解决常见软件设计问题的可复用方案，分为三大类：1. 创建型模式：处理对象创建机制，包括工厂方法、抽象工厂、单例、建造者和原型模式；2. 结构型模式：关注类和对象的组合，包括适配器、桥接、组合、装饰、外观、享元和代理模式；3. 行为型模式：关注对象间的通信，包括责任链、命令、解释器、迭代器、中介者、备忘录、观察者、状态、策略、模板方法和访问者模式。设计模式帮助开发者构建灵活、可复用、易维护的系统。",
        "course_id": "2",
        "category": "软件工程",
        "tags": "设计模式, 创建型模式, 结构型模式, 行为型模式"
    },
    {
        "title": "关系数据库范式",
        "content": "数据库范式是关系数据库设计的指导原则，用于减少数据冗余和提高数据完整性：1. 第一范式(1NF)：每个属性都是原子的，不可再分；2. 第二范式(2NF)：满足1NF，并且所有非主键属性完全依赖于主键；3. 第三范式(3NF)：满足2NF，并且所有非主键属性都不传递依赖于主键；4. BC范式(BCNF)：更严格的3NF，所有决定因素必须是候选键；5. 第四范式(4NF)：处理多值依赖；6. 第五范式(5NF)：处理连接依赖。实际设计中，通常以满足3NF或BCNF为目标，有时会适当反规范化以提高查询性能。",
        "course_id": "2",
        "category": "数据库",
        "tags": "关系数据库, 数据库范式, 数据库设计, 数据完整性"
    },
    {
        "title": "SQL查询优化技术",
        "content": "SQL查询优化的关键技术：1. 合理使用索引：为常用查询条件和连接列创建适当索引，但避免过度索引；2. 查询重写：简化复杂查询，避免子查询，使用连接替代IN；3. 避免全表扫描：使用EXPLAIN分析执行计划；4. 限制结果集大小：使用LIMIT子句；5. 避免使用SELECT *：只选择需要的列；6. 使用合适的表连接方式；7. 分区技术：对大表进行水平或垂直分区；8. 合理使用视图和存储过程；9. 定期更新统计信息和优化数据库参数；10. 考虑数据分布和缓存策略。",
        "course_id": "2",
        "category": "数据库",
        "tags": "SQL优化, 查询性能, 索引设计, 执行计划"
    },
    {
        "title": "分布式系统CAP定理",
        "content": "CAP定理是分布式系统设计的基本原则，指出一个分布式系统无法同时满足以下三个特性：1. 一致性(Consistency)：所有节点在同一时间具有相同的数据；2. 可用性(Availability)：每个请求都能得到响应，无论成功或失败；3. 分区容错性(Partition tolerance)：系统在网络分区故障时仍能继续运行。实际系统中，必须在这三者间做出权衡：CP系统(如HBase、MongoDB)优先保证一致性；AP系统(如Cassandra、DynamoDB)优先保证可用性；CA系统在实际分布式环境中几乎不存在，因为网络分区是不可避免的。",
        "course_id": "3",
        "category": "分布式系统",
        "tags": "CAP定理, 分布式系统, 一致性, 可用性, 容错性"
    },
    {
        "title": "分布式一致性协议",
        "content": "分布式一致性协议用于确保分布式系统中的多个节点就某个值达成一致：1. Paxos算法：最早的理论完备的一致性算法，复杂且难以实现；2. Raft算法：为可理解性设计的一致性算法，通过领导者选举、日志复制和安全性保证实现一致性；3. ZAB(Zookeeper Atomic Broadcast)：Zookeeper使用的原子广播协议；4. 两阶段提交(2PC)：通过准备和提交两个阶段确保事务的原子性，但存在单点故障问题；5. 三阶段提交(3PC)：2PC的改进版，增加了预提交阶段；6. 拜占庭将军问题：处理可能存在恶意节点的极端情况。",
        "course_id": "3",
        "category": "分布式系统",
        "tags": "一致性协议, Paxos, Raft, 拜占庭容错, 共识算法"
    },
    {
        "title": "机器学习模型评估指标",
        "content": "选择合适的评估指标对机器学习模型至关重要：1. 分类问题：准确率(Accuracy)、精确率(Precision)、召回率(Recall)、F1分数、ROC曲线、AUC值、混淆矩阵；2. 回归问题：均方误差(MSE)、均方根误差(RMSE)、平均绝对误差(MAE)、R²值、调整R²；3. 聚类问题：轮廓系数、Davies-Bouldin指数、Calinski-Harabasz指数、互信息；4. 排序问题：NDCG、MAP、MRR。评估还应考虑模型复杂度、训练时间和推理时间等因素。交叉验证是防止过拟合的重要技术，特别是在数据集有限时。",
        "course_id": "3",
        "category": "机器学习",
        "tags": "模型评估, 评估指标, 分类指标, 回归指标, 过拟合"
    },
    {
        "title": "深度学习架构与应用",
        "content": "深度学习架构及其典型应用：1. 卷积神经网络(CNN)：图像识别、物体检测、分割；2. 循环神经网络(RNN)和LSTM：序列处理、时间序列预测、语言建模；3. 变换器(Transformer)：自然语言处理、机器翻译、问答系统；4. 生成对抗网络(GAN)：图像生成、风格迁移、数据增强；5. 自编码器：降维、特征学习、异常检测；6. 图神经网络(GNN)：社交网络分析、分子结构预测；7. 强化学习网络：游戏AI、机器人控制、资源调度。各架构的选择取决于数据类型、问题复杂度、可用计算资源和解释性需求。",
        "course_id": "3",
        "category": "机器学习",
        "tags": "深度学习, CNN, RNN, Transformer, GAN, 神经网络应用"
    }
]

def add_knowledge(entry):
    """Add a knowledge entry to the knowledge base"""
    url = f"{BASE_URL}/search/add"
    
    try:
        response = session.post(url, data=entry)
        
        # Check if the request was successful
        if response.status_code == 200 and "知识条目已添加" in response.text:
            print(f"Successfully added: {entry['title']}")
            return True
        else:
            print(f"Failed to add: {entry['title']}")
            print(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error adding knowledge entry: {e}")
        return False

def main():
    print(f"Starting to add {len(knowledge_entries)} knowledge entries...")
    
    success_count = 0
    for entry in knowledge_entries:
        if add_knowledge(entry):
            success_count += 1
        
        # Add a short delay between requests to avoid overwhelming the server
        time.sleep(1)
    
    print(f"Completed! Added {success_count}/{len(knowledge_entries)} knowledge entries.")

if __name__ == "__main__":
    main() 