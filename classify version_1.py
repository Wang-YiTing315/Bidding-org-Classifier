import pandas as pd
import requests
from tqdm import tqdm
import time

API_KEY = "your deepseek api"
API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_categories(purchaser_names):
    """让API总结10个最合适的分类（含其他），返回类别列表"""
    prompt = (
        f"以下是{len(purchaser_names)}个采购方名称，请你根据内容总结出10个最合适的分类（其中一个为'其他'），"
        "只返回10个分类名称，用中文，用逗号分隔，不要解释：\n"
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
        # 只保留逗号分隔的前10个
        cats = [c.strip() for c in content.replace('，', ',').split(',') if c.strip()]
        return cats[:10]
    except Exception as e:
        print("API调用出错:", e)
        # 默认10个类别
        return ["政府机构", "教育机构", "医疗机构", "企业", "科研机构", "交通运输", "执法机构", "文化机构", "公共服务", "其他"]

def classify(name, categories):
    """让API判断name属于哪个类别，只返回类别名称"""
    prompt = (
        f"已知类别有：{','.join(categories)}。请判断'{name}'最适合归入哪个类别，只返回类别名称。"
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
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("API调用出错:", e)
        return "其他"

def main():
    # 读取Excel
    df = pd.read_excel("30个样例，只保留国家买方和概括.xlsx")  # 请替换为你的实际文件名
    purchaser_names = df['Purchaser_Name'].astype(str).tolist()

    # 第一步：获取10个类别
    print("正在获取10个最合适的分类...")
    categories = get_categories(purchaser_names)
    print("API返回的分类：", categories)

    # 第二步：逐条归类
    print("正在对每条数据进行归类...")
    classifications = []
    pbar = tqdm(total=len(df), desc="处理进度")
    for name in purchaser_names:
        result = classify(name, categories)
        # 只保留在categories里的类别，否则归为"其他"
        if result not in categories:
            result = "其他"
        classifications.append(result)
        pbar.update(1)
        time.sleep(0.5)
    pbar.close()

    df['Classification'] = classifications
    df.to_excel("classify.xlsx", index=False)
    print("分类完成，结果已保存到 classify.xlsx")

if __name__ == "__main__":
    main()
