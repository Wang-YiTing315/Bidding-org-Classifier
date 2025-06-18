# 招投标机构智能分类系统

## 项目概述

本项目是一个基于AI的招投标机构智能分类系统，通过分析采购方名称，自动将其归类到最合适的业务类别中。系统采用迭代优化策略，确保分类结果的准确性和均衡性。

## 核心功能

### 🎯 主要特性
- **智能分类生成**：基于数据特征自动生成10个最合适的业务分类
- **质量评估体系**：采用多维度评分机制，确保分类质量
- **迭代优化**：通过多次抽样和评估，持续优化分类结果
- **错误处理机制**：完善的网络重试和异常处理
- **均衡性保证**：确保各类别分布合理，避免过度集中

### 📊 评估指标
- **最大类别占比**（30分）：避免单一类别过度集中
- **其他类别占比**（25分）：控制"其他"类别的比例
- **最小类别占比**（20分）：确保小类别有合理分布
- **分布均衡性**（25分）：基于基尼系数的均衡性评估

## 版本演进历程

### Version 1.0 - 基础版本
**文件：** `classify version_1.py`

**特点：**
- 简单的分类生成和匹配
- 基础错误处理
- 直接处理全量数据
- 无质量评估机制

**技术实现：**
```python
# 生成10个分类
categories = get_categories(purchaser_names)

# 逐条分类
for name in purchaser_names:
    result = classify(name, categories)
```

**局限性：**
- 分类质量不可控
- 无分布均衡性考虑
- 错误处理简单

### Version 2.0 - 描述增强版
**文件：** `classify version_2.py`

**改进：**
- 为每个分类添加详细描述
- 基于描述的精确分类
- 改进的API调用机制

**技术实现：**
```python
# 生成分类及描述
num2name, num2desc = get_categories_with_desc(purchaser_names)

# 基于描述的分类
result = classify_with_desc(name, num2name, num2desc)
```

**优势：**
- 分类更精确
- 描述提供上下文
- 减少分类歧义

### Version 3.0 - 质量评估版
**文件：** `classify version_3.py`

**重大改进：**
- 引入质量评估体系
- 多维度评分机制
- 基尼系数均衡性评估
- 详细的评估报告

**核心功能：**
```python
def evaluate_classification_quality(classifications):
    # 最大类别占比评分 (30分)
    # 其他类别占比评分 (25分)
    # 最小类别占比评分 (20分)
    # 分布均衡性评分 (25分)
```

**评估标准：**
- 优秀：80分以上
- 良好：70-79分
- 一般：60-69分
- 较差：50-59分
- 很差：50分以下

### Version 4.0 - 迭代优化版 ⭐
**文件：** `classify version_4.py`

**最终版本特性：**
- **迭代抽样策略**：500样本生成分类 + 500样本质量检验
- **严格质量标准**：90分以上才算合格
- **完善错误处理**：SSL重试、网络超时、指数退避
- **智能重试机制**：自动处理网络异常
- **高质量保证**：确保分类结果达到优秀标准

**技术亮点：**
```python
# 创建带有重试机制的session
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# 迭代优化流程
while iteration <= max_iterations:
    # 第一次抽样：生成分类
    sample_names_1 = random.sample(purchaser_names, 500)
    num2name, num2desc = get_categories_with_desc(sample_names_1)
    
    # 第二次抽样：质量检验
    sample_names_2 = random.sample(remaining_names, 500)
    evaluation_report = evaluate_classification_quality(sample_classifications)
    
    if evaluation_report['总分'] >= 90:
        break  # 达到质量标准
```

## 技术架构

### 🔧 核心技术栈
- **Python 3.x**：主要开发语言
- **pandas**：数据处理和分析
- **requests**：HTTP API调用
- **tqdm**：进度条显示
- **numpy**：数学计算
- **collections.Counter**：数据统计

### 🌐 API集成
- **DeepSeek API**：AI分类服务
- **模型**：deepseek-chat
- **温度参数**：0.3（确保结果稳定性）

### 📈 质量评估算法
- **基尼系数**：衡量分布均衡性
- **百分比分析**：各类别占比统计
- **综合评分**：多维度质量评估

## 使用方法

### 环境准备
```bash
pip install pandas requests tqdm numpy
```

### 数据格式
Excel文件需包含 `Purchaser_Name` 列，包含采购方名称。

### 运行程序
```bash
python "classify version_4.py"
```

### 输出结果
- `classify.xlsx`：包含分类结果的Excel文件
- 控制台输出：详细的评估报告和进度信息

## 项目亮点

### 🎯 智能优化
- 自动生成最适合的分类体系
- 基于数据特征的动态分类调整
- 迭代优化确保最佳结果

### 📊 质量保证
- 严格的90分质量标准
- 多维度评估体系
- 均衡性自动调整

### 🔄 鲁棒性
- 完善的错误处理机制
- 网络异常自动重试
- 指数退避策略

### 📈 可扩展性
- 模块化设计
- 易于添加新的评估指标
- 支持不同数据源

## 版本对比总结

| 版本 | 核心特性 | 质量保证 | 错误处理 | 推荐度 |
|------|----------|----------|----------|--------|
| v1.0 | 基础分类 | ❌ | 简单 | ⭐⭐ |
| v2.0 | 描述增强 | ❌ | 基础 | ⭐⭐⭐ |
| v3.0 | 质量评估 | ✅ | 改进 | ⭐⭐⭐⭐ |
| v4.0 | 迭代优化 | ✅✅ | 完善 | ⭐⭐⭐⭐⭐ |

## 未来发展方向

- [ ] 支持更多AI模型
- [ ] 添加可视化界面
- [ ] 支持实时分类API
- [ ] 增加更多评估维度
- [ ] 支持多语言分类

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 许可证

MIT License

---

**推荐使用 Version 4.0** - 这是目前最完善、最稳定的版本，具有最好的分类质量和错误处理能力。 
