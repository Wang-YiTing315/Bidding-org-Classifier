#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发功能测试脚本
用于验证get_class.py和classify.py的并发处理功能
"""

import time
import json
from get_class import classify_sample_data_concurrent, get_categories_with_desc
from classify import classify_all_data_concurrent, load_categories_from_json

def test_concurrent_classification():
    """
    测试并发分类功能
    """
    print("🧪 开始测试并发分类功能...")
    print("="*60)
    
    # 测试数据
    test_names = [
        "北京市政府",
        "清华大学",
        "北京大学第一医院",
        "中国石油化工股份有限公司",
        "中国科学院",
        "中国铁路总公司",
        "北京市公安局",
        "国家图书馆",
        "北京市自来水公司",
        "其他测试机构"
    ]
    
    print(f"📊 测试数据量: {len(test_names)}")
    print(f"📋 测试数据: {test_names}")
    
    # 1. 测试生成分类
    print("\n🔍 测试1: 生成分类...")
    start_time = time.time()
    num2name, num2desc = get_categories_with_desc(test_names)
    end_time = time.time()
    print(f"✅ 分类生成完成，耗时: {end_time - start_time:.2f}秒")
    
    print("📋 生成的分类:")
    for num in sorted(num2name.keys()):
        print(f"   {num}: {num2name[num]} - {num2desc[num]}")
    
    # 2. 测试并发分类
    print("\n🔍 测试2: 并发分类...")
    start_time = time.time()
    classifications = classify_sample_data_concurrent(test_names, num2name, num2desc, max_workers=3)
    end_time = time.time()
    print(f"✅ 并发分类完成，耗时: {end_time - start_time:.2f}秒")
    
    print("📊 分类结果:")
    for i, (name, classification) in enumerate(zip(test_names, classifications)):
        print(f"   {i+1}. {name} -> {classification}")
    
    # 3. 测试全量数据并发分类
    print("\n🔍 测试3: 全量数据并发分类...")
    start_time = time.time()
    all_classifications = classify_all_data_concurrent(test_names, num2name, num2desc, max_workers=3)
    end_time = time.time()
    print(f"✅ 全量并发分类完成，耗时: {end_time - start_time:.2f}秒")
    
    print("📊 全量分类结果:")
    for i, (name, classification) in enumerate(zip(test_names, all_classifications)):
        print(f"   {i+1}. {name} -> {classification}")
    
    # 4. 验证结果一致性
    print("\n🔍 测试4: 验证结果一致性...")
    if classifications == all_classifications:
        print("✅ 并发分类结果一致")
    else:
        print("❌ 并发分类结果不一致")
        print(f"抽样分类: {classifications}")
        print(f"全量分类: {all_classifications}")
    
    print("\n🎉 并发功能测试完成！")

def test_performance_comparison():
    """
    测试性能对比
    """
    print("\n" + "="*60)
    print("📈 性能对比测试")
    print("="*60)
    
    # 创建更多测试数据
    test_names = [
        "北京市政府", "清华大学", "北京大学第一医院", "中国石油化工股份有限公司",
        "中国科学院", "中国铁路总公司", "北京市公安局", "国家图书馆",
        "北京市自来水公司", "其他测试机构", "上海市政府", "复旦大学",
        "上海交通大学医学院附属瑞金医院", "中国移动通信集团有限公司",
        "中国科学技术大学", "中国民用航空局", "上海市公安局", "上海图书馆",
        "上海市自来水公司", "测试机构A"
    ]
    
    print(f"📊 测试数据量: {len(test_names)}")
    
    # 生成分类
    num2name, num2desc = get_categories_with_desc(test_names[:5])  # 只用前5个生成分类
    
    # 测试单线程性能
    print("\n🔍 单线程性能测试...")
    start_time = time.time()
    from get_class import classify_with_desc
    single_thread_results = []
    for name in test_names:
        result = classify_with_desc(name, num2name, num2desc)
        single_thread_results.append(result)
    single_thread_time = time.time() - start_time
    print(f"⏱️ 单线程耗时: {single_thread_time:.2f}秒")
    
    # 测试并发性能
    print("\n🔍 并发性能测试...")
    start_time = time.time()
    concurrent_results = classify_sample_data_concurrent(test_names, num2name, num2desc, max_workers=5)
    concurrent_time = time.time() - start_time
    print(f"⏱️ 并发耗时: {concurrent_time:.2f}秒")
    
    # 计算性能提升
    speedup = single_thread_time / concurrent_time
    print(f"🚀 性能提升: {speedup:.2f}x")
    print(f"⏱️ 节省时间: {single_thread_time - concurrent_time:.2f}秒")
    
    # 验证结果一致性
    if single_thread_results == concurrent_results:
        print("✅ 单线程和并发结果一致")
    else:
        print("❌ 单线程和并发结果不一致")

if __name__ == "__main__":
    print("🎯 招投标机构分类系统 - 并发功能测试")
    print("="*60)
    
    try:
        # 基础功能测试
        test_concurrent_classification()
        
        # 性能对比测试
        test_performance_comparison()
        
        print("\n🎉 所有测试完成！")
        print("💡 提示：如果测试通过，说明并发功能正常工作")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 