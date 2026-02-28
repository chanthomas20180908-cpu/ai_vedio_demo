"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：parse_i2v_prompts.py
"""

import json
import re

def parse_prompt_file(file_path):
    """解析包含多个模型响应的提示词文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 直接从原文件按行读取，找到JSON数组的开始和结束
    lines = content.split('\n')
    
    models_data = []
    current_model = None
    json_start = -1
    bracket_count = 0
    json_lines = []
    
    for i, line in enumerate(lines):
        # 检测模型开始
        if "'model': 'qwen-plus'" in line:
            current_model = 'qwen-plus'
            json_start = -1
            json_lines = []
            bracket_count = 0
        elif "'model': 'deepseek-v3.2'" in line:
            current_model = 'deepseek-v3.2'
            json_start = -1
            json_lines = []
            bracket_count = 0
        
        # 收集JSON内容
        if current_model and json_start == -1:
            # 寻找数组开始
            if line.strip().startswith('['):
                json_start = i
                bracket_count = line.count('[') - line.count(']')
                json_lines.append(line.strip())
        elif current_model and json_start >= 0:
            json_lines.append(line.strip())
            bracket_count += line.count('[') - line.count(']')
            
            # 数组结束
            if bracket_count == 0 and ']' in line:
                # 合并并解析
                json_str = '\n'.join(json_lines)
                try:
                    data = json.loads(json_str)
                    models_data.append((current_model, data))
                except Exception as e:
                    print(f"解析 {current_model} 失败: {e}")
                current_model = None
                json_start = -1
                json_lines = []
    
    return models_data

def get_specific_prompts(file_path):
    """提取3个最佳表情包提示词"""
    models_data = parse_prompt_file(file_path)
    
    selected_prompts = {}
    
    for model_name, prompts_list in models_data:
        if model_name == 'qwen-plus' and len(prompts_list) > 0:
            # 蒸汽喷发式暴怒 (第1个)
            selected_prompts['steam_rage'] = json.dumps(prompts_list[0], ensure_ascii=False)
        
        elif model_name == 'deepseek-v3.2':
            if len(prompts_list) > 0:
                # 委屈核爆 (第1个)
                selected_prompts['sad_nuke'] = json.dumps(prompts_list[0], ensure_ascii=False)
            if len(prompts_list) > 4:
                # 表情包格式崩坏 (第5个)
                selected_prompts['glitch'] = json.dumps(prompts_list[4], ensure_ascii=False)
    
    return selected_prompts

if __name__ == "__main__":
    input_file = "/Users/thomaschan/Code/My_files/my_files/my_draft/test_txt/i2v_prompt_res_20251219-184400.txt"
    
    prompts = get_specific_prompts(input_file)
    
    print("=" * 60)
    print("提取的3个提示词:")
    print("=" * 60)
    
    for key, prompt in prompts.items():
        print(f"\n{key}:")
        print(f"长度: {len(prompt)} 字符")
        print(f"预览: {prompt[:200]}...")
    
    # 保存到文件供后续使用
    # output_file = "/Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/debug/extracted_prompts.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n已保存到: {output_file}")
