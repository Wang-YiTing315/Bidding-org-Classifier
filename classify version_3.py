import pandas as pd
import requests
from tqdm import tqdm
import time
import random
import numpy as np
from collections import Counter

API_KEY = "your deepseek api key"
API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_categories_with_desc(purchaser_names):
    """
    让API总结10个最合适的分类（含其他），并为每个类别写一句简要解释。
    返回：编号到名称的映射、编号到解释的映射
    """
    prompt = (
        f"以下是{len(purchaser_names)}个采购方名称，请你根据内容总结出10个最合适的分类（其中一个为'其他'），"
        "并为每个类别写一句简要解释。请用如下格式输出：\n"
        "类别1：政府机构：负责行政管理的机构\n类别2：教育机构：负责教育教学的机构\n...（用中文，不要其他内容）\n"
        + "\n".join(purchaser_names)
    )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        # 解析编号、名称和解释
        lines = [line for line in content.split('\n') if '：' in line or ':' in line]
        num2name, num2desc = {}, {}
        for line in lines:
            parts = line.replace('：', ':').split(':')
            if len(parts) >= 3:
                num, name, desc = parts[0].strip(), parts[1].strip(), parts[2].strip()
            elif len(parts) == 2:
                num, name, desc = parts[0].strip(), parts[1].strip(), ""
            else:
                continue
            num2name[num] = name
            num2desc[num] = desc
        return num2name, num2desc
    except Exception as e:
        print("API调用出错:", e)
        # 默认
        num2name = {
            "类别1": "政府机构", "类别2": "教育机构", "类别3": "医疗机构", "类别4": "企业", "类别5": "科研机构",
            "类别6": "交通运输", "类别7": "执法机构", "类别8": "文化机构", "类别9": "公共服务", "类别10": "其他"
        }
        num2desc = {
            "类别1": "负责行政管理的机构", "类别2": "负责教育教学的机构", "类别3": "提供医疗服务的机构", "类别4": "各类企业公司",
            "类别5": "从事科学研究的机构", "类别6": "负责交通运输的单位", "类别7": "执法和安全相关机构",
            "类别8": "文化宣传和活动相关机构", "类别9": "提供公共服务的单位", "类别10": "不属于以上类别的其他机构"
        }
        return num2name, num2desc

def classify_with_desc(name, num2name, num2desc):
    # 将所有类别编号、类别名称和类别描述组成一个字符串（每个类别的描述一行）
    cat_desc_str = "\n".join([f"{num}:{num2name[num]}：{num2desc[num]}" for num in num2name])
    prompt = (
        f"""已知有如下类别及解释：\n{cat_desc_str}\n请判断\"{name}\"最适合归入哪个类别，只返回类别编号，如'类别10'、'类别5'，不要其他解释。"""
    )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        # 发送 POST 请求到 API URL，获取 API 的响应
        response = requests.post(API_URL, headers=headers, json=data)
        # 如果请求失败，抛出异常
        response.raise_for_status()
        # 从返回的 JSON 中提取类别编号并去除多余的空白字符
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        # 如果请求过程中出现异常，打印错误信息，并返回默认类别 '类别10'
        print("API调用出错:", e)
        return "类别10"

def evaluate_classification_quality(classifications):
    """
    评估分类质量的函数，使用积分制量化评估
    返回：总分、各项得分详情
    """
    # 统计各类别数量
    class_counts = Counter(classifications)
    total_count = len(classifications)
    
    # 计算各类别占比
    class_percentages = {k: v/total_count*100 for k, v in class_counts.items()}
    
    # 1. 最大类别占比评分 (满分30分)
    max_class_percentage = max(class_percentages.values())
    if max_class_percentage <= 20:  # 最大类不超过20%，优秀
        max_class_score = 30
    elif max_class_percentage <= 30:  # 最大类20-30%，良好
        max_class_score = 25
    elif max_class_percentage <= 40:  # 最大类30-40%，一般
        max_class_score = 20
    elif max_class_percentage <= 50:  # 最大类40-50%，较差
        max_class_score = 15
    else:  # 最大类超过50%，很差
        max_class_score = 10
    
    # 2. "其他"类别占比评分 (满分25分)
    other_percentage = class_percentages.get("其他", 0)
    if other_percentage <= 5:  # "其他"类不超过5%，优秀
        other_class_score = 25
    elif other_percentage <= 10:  # "其他"类5-10%，良好
        other_class_score = 20
    elif other_percentage <= 15:  # "其他"类10-15%，一般
        other_class_score = 15
    elif other_percentage <= 20:  # "其他"类15-20%，较差
        other_class_score = 10
    else:  # "其他"类超过20%，很差
        other_class_score = 5
    
    # 3. 最小类别占比评分 (满分20分)
    min_class_percentage = min(class_percentages.values())
    if min_class_percentage >= 3:  # 最小类至少3%，优秀
        min_class_score = 20
    elif min_class_percentage >= 2:  # 最小类2-3%，良好
        min_class_score = 16
    elif min_class_percentage >= 1:  # 最小类1-2%，一般
        min_class_score = 12
    elif min_class_percentage >= 0.5:  # 最小类0.5-1%，较差
        min_class_score = 8
    else:  # 最小类少于0.5%，很差
        min_class_score = 4
    
    # 4. 类别分布均衡性评分 (满分25分) - 使用基尼系数
    percentages = list(class_percentages.values())
    gini_coefficient = calculate_gini_coefficient(percentages)
    if gini_coefficient <= 0.3:  # 分布很均衡
        balance_score = 25
    elif gini_coefficient <= 0.4:  # 分布较均衡
        balance_score = 20
    elif gini_coefficient <= 0.5:  # 分布一般
        balance_score = 15
    elif gini_coefficient <= 0.6:  # 分布不均衡
        balance_score = 10
    else:  # 分布很不均衡
        balance_score = 5
    
    # 计算总分
    total_score = max_class_score + other_class_score + min_class_score + balance_score
    
    # 生成评估报告
    evaluation_report = {
        "总分": total_score,
        "评分详情": {
            "最大类别占比评分": max_class_score,
            "其他类别占比评分": other_class_score,
            "最小类别占比评分": min_class_score,
            "分布均衡性评分": balance_score
        },
        "统计数据": {
            "总数据量": total_count,
            "类别数量": len(class_counts),
            "最大类别占比": f"{max_class_percentage:.2f}%",
            "其他类别占比": f"{other_percentage:.2f}%",
            "最小类别占比": f"{min_class_percentage:.2f}%",
            "基尼系数": f"{gini_coefficient:.3f}"
        },
        "各类别分布": class_percentages
    }
    
    return evaluation_report

def calculate_gini_coefficient(values):
    """
    计算基尼系数，用于衡量分布的不均衡程度
    基尼系数越小，分布越均衡
    """
    if len(values) == 0:
        return 0
    
    values = sorted(values)
    n = len(values)
    cumsum = np.cumsum(values)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

def print_evaluation_report(report, iteration=None):
    """
    打印评估报告
    """
    if iteration:
        print(f"\n" + "="*60)
        print(f"第{iteration}次抽样分类质量评估报告")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("最终分类质量评估报告")
        print("="*60)
    
    print(f"\n📊 总体评分: {report['总分']}/100分")
    
    if report['总分'] >= 80:
        grade = "优秀"
    elif report['总分'] >= 70:
        grade = "良好"
    elif report['总分'] >= 60:
        grade = "一般"
    elif report['总分'] >= 50:
        grade = "较差"
    else:
        grade = "很差"
    
    print(f"🏆 等级评定: {grade}")
    
    print(f"\n📈 评分详情:")
    for item, score in report['评分详情'].items():
        print(f"   {item}: {score}分")
    
    print(f"\n📋 统计数据:")
    for item, value in report['统计数据'].items():
        print(f"   {item}: {value}")
    
    print(f"\n📊 各类别分布:")
    for class_name, percentage in sorted(report['各类别分布'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {class_name}: {percentage:.2f}%")
    
    print("="*60)

def classify_sample_data(sample_names, num2name, num2desc):
    """
    对抽样数据进行分类
    """
    classifications = []
    pbar = tqdm(total=len(sample_names), desc="抽样数据分类进度")
    for name in sample_names:
        result = classify_with_desc(name, num2name, num2desc)
        result_clean = result.replace('：', ':').split(':')[0].strip()  # 只保留编号
        final_label = num2name.get(result_clean, "其他")
        classifications.append(final_label)
        pbar.update(1)
        time.sleep(0.5)
    pbar.close()
    return classifications

def main():
    df = pd.read_excel("合并后的表格.xlsx")
    purchaser_names = df['Purchaser_Name'].astype(str).tolist()
    
    print(f"总数据量: {len(purchaser_names)}")
    
    # 设置随机种子确保结果可重现
    random.seed(42)
    
    # 迭代抽样和分类质量检验
    iteration = 1
    max_iterations = 5  # 最大迭代次数，避免无限循环
    quality_threshold = 80  # 质量阈值，达到80分即可
    
    while iteration <= max_iterations:
        print(f"\n🔄 第{iteration}次迭代开始...")
        
        # 第一次抽样：生成分类
        print("📝 第一次抽样：生成10个分类...")
        if len(purchaser_names) > 500:
            sample_names_1 = random.sample(purchaser_names, 500)
            print(f"已随机抽样500个数据用于生成分类")
        else:
            sample_names_1 = purchaser_names
            print(f"数据量({len(purchaser_names)})未超过500个，使用全部数据生成分类")
        
        # 获取分类
        print("正在获取10个最合适的分类及解释...")
        num2name, num2desc = get_categories_with_desc(sample_names_1)
        print("API返回的分类及解释：")
        for num in num2name:
            print(f"{num}: {num2name[num]} - {num2desc[num]}")
        
        # 第二次抽样：检验分类质量
        print("\n🔍 第二次抽样：检验分类质量...")
        # 从剩余数据中抽样，避免重复
        remaining_names = [name for name in purchaser_names if name not in sample_names_1]
        if len(remaining_names) >= 500:
            sample_names_2 = random.sample(remaining_names, 500)
            print(f"已从剩余数据中随机抽样500个数据用于质量检验")
        elif len(remaining_names) > 0:
            sample_names_2 = remaining_names
            print(f"剩余数据量({len(remaining_names)})不足500个，使用全部剩余数据进行质量检验")
        else:
            # 如果剩余数据不足，从全部数据中重新抽样，但不超过总数据量
            sample_size = min(500, len(purchaser_names))
            sample_names_2 = random.sample(purchaser_names, sample_size)
            print(f"剩余数据不足，重新从全部数据中抽样{sample_size}个进行质量检验")
        
        # 对第二次抽样数据进行分类
        print("正在对第二次抽样数据进行分类...")
        sample_classifications = classify_sample_data(sample_names_2, num2name, num2desc)
        
        # 评估分类质量
        print("正在评估分类质量...")
        evaluation_report = evaluate_classification_quality(sample_classifications)
        print_evaluation_report(evaluation_report, iteration)
        
        # 检查是否达到质量标准
        if evaluation_report['总分'] >= quality_threshold:
            print(f"\n✅ 分类质量达到标准({evaluation_report['总分']}分 >= {quality_threshold}分)，开始对全量数据进行分类...")
            break
        else:
            print(f"\n❌ 分类质量未达到标准({evaluation_report['总分']}分 < {quality_threshold}分)，准备进行第{iteration+1}次迭代...")
            iteration += 1
            if iteration > max_iterations:
                print(f"⚠️ 已达到最大迭代次数({max_iterations})，使用当前分类结果进行全量分类")
                break
    
    # 对全量数据进行分类
    print("\n🚀 开始对全量数据进行分类...")
    all_classifications = []
    pbar = tqdm(total=len(df), desc="全量数据分类进度")
    for name in purchaser_names:
        result = classify_with_desc(name, num2name, num2desc)
        result_clean = result.replace('：', ':').split(':')[0].strip()  # 只保留编号
        final_label = num2name.get(result_clean, "其他")
        all_classifications.append(final_label)
        pbar.update(1)
        time.sleep(0.5)
    pbar.close()

    df['Classification'] = all_classifications
    df.to_excel("classify.xlsx", index=False)
    print("分类完成，结果已保存到 classify.xlsx")
    
    # 最终评估
    print("\n正在评估最终分类质量...")
    final_evaluation_report = evaluate_classification_quality(all_classifications)
    print_evaluation_report(final_evaluation_report)

if __name__ == "__main__":
    main()
