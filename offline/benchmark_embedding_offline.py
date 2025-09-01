import json
import torch
import time
import argparse
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

def get_chunks(input_file):
    with open(input_file, "r", encoding='utf8') as f:
        chunks = json.load(f)
    return chunks

def last_token_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def data_iterator(sample_texts, batch_size=4):
    count = 0
    batch = []
    max_samples = len(sample_texts)
    while count < max_samples:
        for text in sample_texts:
            batch.append(text)
            if len(batch) == batch_size:
                yield batch
                batch = []
                count += batch_size
        if batch:
            yield batch
            count += len(batch)
            batch = []

def benchmark(input_file, model_path, device):
    if device == "hpu":
        import habana_frameworks.torch as ht
        import habana_frameworks.torch.core as htcore

    tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side='left')
    model = AutoModel.from_pretrained(model_path)

    if device == "hpu":
        model = model.to("hpu")
        model = ht.hpu.wrap_in_hpu_graph(model)
        print("Using HPU device")
    else:
        model = model.to("cpu")
        print("Using CPU device")

    chunks = get_chunks(input_file)

    total_texts = 0
    total_tokens = 0
    total_time = 0.0
    batch_count = 0

    warmup_text = ["warmup text"] * 3
    batch_dict = tokenizer(
        warmup_text,
        padding="longest",
        pad_to_multiple_of=256,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    batch_dict.to(model.device)
    outputs = model(**batch_dict)
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

    if device == "hpu":
        htcore.mark_step()
        htcore.hpu.synchronize()

    print(f"Starting benchmark with {len(chunks)} texts...")
    start_time = time.time()

    for batch_texts in data_iterator(chunks, batch_size=3):
        batch_count += 1
        print(f"\nProcessing batch #{batch_count} of size {len(batch_texts)}")
        total_texts += len(batch_texts)

        batch_start_time = time.time()

        # Tokenization
        tokenize_start = time.time()
        batch_dict = tokenizer(
            batch_texts,
            padding="longest",
            pad_to_multiple_of=256,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        tokenize_time = time.time() - tokenize_start

        batch_token_count = batch_dict['input_ids'].numel()
        total_tokens += batch_token_count

        batch_dict.to(model.device)
        model_start = time.time()
        outputs = model(**batch_dict)
        embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

        if device == "hpu":
            htcore.mark_step()
            htcore.hpu.synchronize()

        model_time = time.time() - model_start

        batch_time = time.time() - batch_start_time
        total_time += batch_time

        texts_per_sec = len(batch_texts) / batch_time
        tokens_per_sec = batch_token_count / batch_time

        print(f"  Token count: {batch_token_count} tokens")
        print(f"  Batch time: {batch_time:.4f}s (tokenize: {tokenize_time:.4f}s, model: {model_time:.4f}s)")
        print(f"  Throughput: {texts_per_sec:.2f} texts/sec | {tokens_per_sec:.2f} tokens/sec")

    end_time = time.time()
    total_duration = end_time - start_time
    avg_texts_per_sec = total_texts / total_duration
    avg_tokens_per_sec = total_tokens / total_duration

    print("\n" + "="*50)
    print("Benchmark Summary:")
    print(f"  Device: {device.upper()}")
    print(f"  Total texts processed: {total_texts}")
    print(f"  Total tokens processed: {total_tokens}")
    print(f"  Total batches: {batch_count}")
    print(f"  Total time: {total_duration:.2f} seconds")
    print(f"  Average throughput: {avg_texts_per_sec:.2f} texts/sec")
    print(f"  Average throughput: {avg_tokens_per_sec:.2f} tokens/sec")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embedding Model Benchmark")
    parser.add_argument("--input", type=str, default="token_len_500.json", help="Input JSON file path")
    parser.add_argument("--model", type=str, default="/data/Qwen3-Embedding-0.6B/", help="Model path")
    parser.add_argument("--device", type=str, default="hpu", choices=["cpu", "hpu"], help="Device to use: cpu or hpu")
    parser.add_argument("--max_length", type=int, default=8192, help="Maximum token length")

    args = parser.parse_args()

    global max_length
    max_length = args.max_length

    benchmark(args.input, args.model, args.device)