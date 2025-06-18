import pandas as pd
import requests
from tqdm import tqdm
import time

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
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("API调用出错:", e)
        return "类别10"

def main():
    df = pd.read_excel("400+原数据.xlsx")
    purchaser_names = df['Purchaser_Name'].astype(str).tolist()

    print("正在获取10个最合适的分类及解释...")
    num2name, num2desc = get_categories_with_desc(purchaser_names)
    print("API返回的分类及解释：")
    for num in num2name:
        print(f"{num}: {num2name[num]} - {num2desc[num]}")

    print("正在对每条数据进行归类...")
    classifications = []
    pbar = tqdm(total=len(df), desc="处理进度")
    for name in purchaser_names:
        result = classify_with_desc(name, num2name, num2desc)
        result_clean = result.replace('：', ':').split(':')[0].strip()  # 只保留编号
        final_label = num2name.get(result_clean, "其他")
        #print(final_label)
        classifications.append(final_label)
        pbar.update(1)
        time.sleep(0.5)
    pbar.close()

    df['Classification'] = classifications
    df.to_excel("classify.xlsx", index=False)
    print("分类完成，结果已保存到 classify.xlsx")

if __name__ == "__main__":
    main()
