import argparse
import json
from transformers import AutoTokenizer
from typing import List

def split_text_into_chunks(text: str, chunk_size: int, tokenizer) -> List[str]:
    """使用LLM tokenizer将文本按token数分块"""
    tokens = tokenizer.tokenize(text)
    chunks = []

    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunk_text = chunk_text.replace(' ', '')
        chunks.append(chunk_text)
        """Yield successive n-sized chunks from text."""""

    return chunks

def main():
    parser = argparse.ArgumentParser(description='使用LLM tokenizer的中文文本分块工具')
    parser.add_argument('-f', '--file', type=str, required=True, help='输入文件路径')
    parser.add_argument('-n', '--num_tokens', type=int, required=True, help='每个块的token数量')
    parser.add_argument('-o', '--output', type=str, default='output.json', help='输出JSON文件路径')
    parser.add_argument('-m', '--model', type=str, default='bert-base-chinese',
                       help='HuggingFace模型名称(默认: bert-base-chinese)')

    args = parser.parse_args()

    # 初始化tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model)
    except Exception as e:
        print(f"加载tokenizer失败: {e}")
        return

    # 读取输入文件
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"错误：文件 {args.file} 不存在")
        return
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 分块处理
    chunks = split_text_into_chunks(text, args.num_tokens, tokenizer)

    # 保存为JSON
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"成功将文件分块为 {len(chunks)} 个部分，每个部分约 {args.num_tokens} 个token")
        print(f"使用的tokenizer: {args.model}")
        print(f"结果已保存到 {args.output}")
    except Exception as e:
        print(f"保存JSON文件时出错: {e}")

if __name__ == '__main__':
    main()
