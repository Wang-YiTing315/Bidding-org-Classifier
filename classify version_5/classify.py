import pandas as pd
import requests
from tqdm import tqdm
import time
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

API_KEY = "your deepseek api key"
API_URL = "https://api.deepseek.com/v1/chat/completions"

# 线程锁，用于控制API请求频率
request_lock = threading.Lock()

# 创建带有重试机制的session
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # 总重试次数
        backoff_factor=1,  # 重试间隔
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# 全局session
session = create_session()

def load_categories_from_json(filename="categories.json"):
    """
    从JSON文件加载分类结果
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        num2name = categories_data["num2name"]
        num2desc = categories_data["num2desc"]
        timestamp = categories_data.get("timestamp", "未知")
        total_categories = categories_data.get("total_categories", len(num2name))
        
        print(f"✅ 成功加载分类结果")
        print(f"📅 生成时间: {timestamp}")
        print(f"📊 分类数量: {total_categories}")
        
        return num2name, num2desc
    except FileNotFoundError:
        print(f"❌ 找不到分类文件 {filename}")
        print("💡 请先运行 get_class.py 生成分类结果")
        return None, None
    except Exception as e:
        print(f"❌ 加载分类文件失败: {e}")
        return None, None

def classify_single_item(args):
    """
    对单个项目进行分类（用于并发处理）
    """
    name, num2name, num2desc, index = args
    
    # 使用线程锁控制API请求频率
    with request_lock:
        time.sleep(0.1)  # 控制请求频率，避免API限制
    
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
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 发送 POST 请求到 API URL，获取 API 的响应
            response = session.post(API_URL, headers=headers, json=data, timeout=30)
            # 如果请求失败，抛出异常
            response.raise_for_status()
            # 从返回的 JSON 中提取类别编号并去除多余的空白字符
            result = response.json()['choices'][0]['message']['content'].strip()
            result_clean = result.replace('：', ':').split(':')[0].strip()  # 只保留编号
            final_label = num2name.get(result_clean, "其他")
            return index, final_label
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
    
    # 如果所有重试都失败了，返回默认类别
    return index, "其他"

def classify_with_desc(name, num2name, num2desc):
    """
    对单个名称进行分类（兼容单线程版本）
    """
    result = classify_single_item((name, num2name, num2desc, 0))
    return result[1]

def classify_all_data_concurrent(purchaser_names, num2name, num2desc, max_workers=10):
    """
    使用并发对全量数据进行分类
    """
    print(f"\n🚀 开始对全量数据进行并发分类...")
    print(f"📊 总数据量: {len(purchaser_names)}")
    print(f"🔧 使用 {max_workers} 个线程进行并发处理")
    
    # 准备任务参数
    tasks = [(name, num2name, num2desc, i) for i, name in enumerate(purchaser_names)]
    
    all_classifications = [None] * len(purchaser_names)  # 预分配结果列表
    
    # 使用线程池执行并发任务
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_index = {executor.submit(classify_single_item, task): task[3] for task in tasks}
        
        # 使用tqdm显示进度
        with tqdm(total=len(purchaser_names), desc="并发分类进度") as pbar:
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    all_classifications[index] = result
                    pbar.update(1)
                    
                    # 每100条数据显示一次进度
                    if (index + 1) % 100 == 0:
                        print(f"\n📈 已处理 {index + 1}/{len(purchaser_names)} 条数据")
                        
                except Exception as e:
                    index = future_to_index[future]
                    print(f"\n❌ 处理第 {index + 1} 条数据时出错: {e}")
                    all_classifications[index] = "其他"
                    pbar.update(1)
    
    return all_classifications

def classify_all_data(purchaser_names, num2name, num2desc):
    """
    对全量数据进行分类（保持向后兼容）
    """
    # 根据数据量决定是否使用并发
    if len(purchaser_names) > 100:
        # 根据数据量动态调整线程数
        if len(purchaser_names) > 1000:
            max_workers = 15
        elif len(purchaser_names) > 500:
            max_workers = 10
        else:
            max_workers = 5
        return classify_all_data_concurrent(purchaser_names, num2name, num2desc, max_workers)
    else:
        # 小数据量使用单线程
        print(f"\n🚀 开始对全量数据进行分类...")
        print(f"📊 总数据量: {len(purchaser_names)}")
        
        all_classifications = []
        pbar = tqdm(total=len(purchaser_names), desc="全量数据分类进度")
        
        for i, name in enumerate(purchaser_names):
            try:
                result = classify_with_desc(name, num2name, num2desc)
                result_clean = result.replace('：', ':').split(':')[0].strip()  # 只保留编号
                final_label = num2name.get(result_clean, "其他")
                all_classifications.append(final_label)
                
                # 更新进度条
                pbar.update(1)
                
                # 控制请求频率
                time.sleep(0.5)
                
                # 每100条数据显示一次进度
                if (i + 1) % 100 == 0:
                    print(f"\n📈 已处理 {i + 1}/{len(purchaser_names)} 条数据")
                    
            except Exception as e:
                print(f"\n❌ 处理第 {i + 1} 条数据时出错: {e}")
                all_classifications.append("其他")  # 出错时归为"其他"
                pbar.update(1)
        
        pbar.close()
        return all_classifications

def evaluate_final_classification(classifications):
    """
    评估最终分类质量
    """
    from collections import Counter
    import numpy as np
    
    # 统计各类别数量
    class_counts = Counter(classifications)
    total_count = len(classifications)
    
    # 计算各类别占比
    class_percentages = {k: v/total_count*100 for k, v in class_counts.items()}
    
    # 计算基尼系数
    def calculate_gini_coefficient(values):
        if len(values) == 0:
            return 0
        values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(values)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
    
    percentages = list(class_percentages.values())
    gini_coefficient = calculate_gini_coefficient(percentages)
    
    # 生成评估报告
    evaluation_report = {
        "总数据量": total_count,
        "类别数量": len(class_counts),
        "最大类别占比": f"{max(class_percentages.values()):.2f}%",
        "其他类别占比": f"{class_percentages.get('其他', 0):.2f}%",
        "最小类别占比": f"{min(class_percentages.values()):.2f}%",
        "基尼系数": f"{gini_coefficient:.3f}",
        "各类别分布": class_percentages
    }
    
    return evaluation_report

def print_final_report(report):
    """
    打印最终分类报告
    """
    print("\n" + "="*60)
    print("最终分类质量评估报告")
    print("="*60)
    
    print(f"\n📋 统计数据:")
    for item, value in report.items():
        if item != "各类别分布":
            print(f"   {item}: {value}")
    
    print(f"\n📊 各类别分布:")
    for class_name, percentage in sorted(report['各类别分布'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {class_name}: {percentage:.2f}%")
    
    print("="*60)

def main():
    print("🎯 招投标机构分类系统 - 全量数据分类")
    print("="*60)
    
    # 1. 加载分类结果
    categories_file = input("请输入分类文件路径（默认为'categories.json'）: ").strip()
    if not categories_file:
        categories_file = "categories.json"
    
    num2name, num2desc = load_categories_from_json(categories_file)
    if num2name is None or num2desc is None:
        return
    
    # 显示加载的分类
    print(f"\n📋 加载的分类:")
    for num in sorted(num2name.keys()):
        print(f"   {num}: {num2name[num]} - {num2desc[num]}")
    
    # 2. 读取Excel数据
    input_file = input("\n请输入Excel文件路径（默认为'合并后的表格.xlsx'）: ").strip()
    if not input_file:
        input_file = "合并后的表格.xlsx"
    
    try:
        df = pd.read_excel(input_file)
        purchaser_names = df['Purchaser_Name'].astype(str).tolist()
        print(f"✅ 成功读取数据，总数据量: {len(purchaser_names)}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 3. 确认开始分类
    print(f"\n⚠️ 即将开始对 {len(purchaser_names)} 条数据进行分类")
    
    # 根据数据量估算处理时间
    if len(purchaser_names) > 100:
        # 并发处理，速度更快
        estimated_time = len(purchaser_names) * 0.1 / 60  # 0.1秒/条，考虑并发
        print(f"💡 预计耗时: {estimated_time:.1f} 分钟 (并发处理)")
    else:
        # 单线程处理
        estimated_time = len(purchaser_names) * 0.5 / 60
        print(f"💡 预计耗时: {estimated_time:.1f} 分钟 (单线程处理)")
    
    confirm = input("是否继续？(y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print("❌ 用户取消操作")
        return
    
    # 4. 执行分类
    all_classifications = classify_all_data(purchaser_names, num2name, num2desc)
    
    # 5. 保存结果
    df['Classification'] = all_classifications
    
    output_file = input("\n请输入输出文件路径（默认为'classified_result.xlsx'）: ").strip()
    if not output_file:
        output_file = "classified_result.xlsx"
    
    try:
        df.to_excel(output_file, index=False)
        print(f"✅ 分类结果已保存到 {output_file}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return
    
    # 6. 评估最终质量
    print("\n📊 正在评估最终分类质量...")
    final_report = evaluate_final_classification(all_classifications)
    print_final_report(final_report)
    
    # 7. 统计信息
    print(f"\n🎉 分类完成！")
    print(f"📁 输入文件: {input_file}")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 总处理数据: {len(purchaser_names)} 条")
    
    # 根据处理方式显示时间
    if len(purchaser_names) > 100:
        print(f"⏱️ 处理时间: 约 {len(purchaser_names) * 0.1 / 60:.1f} 分钟 (并发处理)")
    else:
        print(f"⏱️ 处理时间: 约 {len(purchaser_names) * 0.5 / 60:.1f} 分钟 (单线程处理)")

if __name__ == "__main__":
    main() 
