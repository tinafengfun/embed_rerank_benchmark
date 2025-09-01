#!/usr/bin/env python3
"""
Script to split Chinese text into fixed-length token chunks using bge-m3 tokenizer.
Output is saved as JSON format with metadata for each chunk.
"""

import argparse
import logging
import json
from typing import List, Dict, Any
from transformers import AutoTokenizer
import sys
import os

def load_bge_m3_tokenizer():
    """Load the bge-m3 tokenizer."""
    try:
        tokenizer = AutoTokenizer.from_pretrained('/model/bge-m3')
        return tokenizer
    except Exception as e:
        logging.error(f"Failed to load bge-m3 tokenizer: {e}")
        logging.info("Attempting to use alternative method...")
        
        # Try using sentence-transformers as fallback
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('BAAI/bge-m3')
            tokenizer = model.tokenizer
            return tokenizer
        except Exception as e2:
            logging.error(f"Failed to load tokenizer via sentence-transformers: {e2}")
            raise

def split_text_into_chunks(text: str, tokenizer, max_length: int) -> List[Dict[str, Any]]:
    """
    Split text into chunks with exactly max_length tokens each.
    
    Args:
        text: Input text to split
        tokenizer: Tokenizer instance
        max_length: Maximum tokens per chunk
        
    Returns:
        List of dictionaries containing chunk data
    """
    # Tokenize the entire text
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    chunks = []
    start_idx = 0
    chunk_id = 0
    
    while start_idx < len(tokens):
        end_idx = min(start_idx + max_length, len(tokens))
        
        # Get the chunk tokens
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        
        # Clean up the chunk
        chunk_text = ' '.join(chunk_text.split())
        
        if chunk_text.strip():
            chunk_data = {
                "id": chunk_id,
                "text": chunk_text,
                "tokens": len(chunk_tokens),
                "start_token": start_idx,
                "end_token": end_idx,
                "original_length": len(chunk_text)
            }
            chunks.append(chunk_data)
            chunk_id += 1
        
        start_idx = end_idx
    
    return chunks

def process_file(input_path: str, output_path: str, tokenizer, max_length: int = 512):
    """
    Process the input file and save tokenized chunks as JSON.
    
    Args:
        input_path: Path to input text file
        output_path: Path to output JSON file
        tokenizer: Tokenizer instance
        max_length: Maximum tokens per chunk
    """
    try:
        # Read the entire file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logging.info(f"Read {len(content)} characters from {input_path}")
        
        # Split into chunks
        chunks = split_text_into_chunks(content, tokenizer, max_length)
        
        # Create metadata
        metadata = {
            "original_file": input_path,
            "total_chunks": len(chunks),
            "max_tokens_per_chunk": max_length,
            "tokenizer": "bge-m3",
            "total_original_chars": len(content),
            "chunks": chunks
        }
        
        # Write JSON to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Created {len(chunks)} chunks, saved to {output_path}")
        
        # Print statistics
        total_tokens = sum(chunk["tokens"] for chunk in chunks)
        avg_tokens = total_tokens / len(chunks) if chunks else 0
        
        logging.info(f"Total tokens processed: {total_tokens}")
        logging.info(f"Average tokens per chunk: {avg_tokens:.2f}")
        
        return chunks
        
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Split text into fixed-length token chunks using bge-m3 tokenizer")
    parser.add_argument("--input_file","-i", help="Input text file path")
    parser.add_argument("--output", "-o", help="Output file path (default: input_file_tokenized.json)")
    parser.add_argument("--length", "-l", type=int, default=512, help="Token length per chunk (default: 512)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Determine output file path
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(args.input_file)[0]
        output_file = f"{base_name}_tokenized.json"
    
    try:
        # Load tokenizer
        logging.info("Loading bge-m3 tokenizer...")
        tokenizer = load_bge_m3_tokenizer()
        logging.info("Tokenizer loaded successfully")
        
        # Process the file
        process_file(args.input_file, output_file, tokenizer, args.length)
        
        print(f"✓ Successfully processed file. Output saved to: {output_file}")
        
    except Exception as e:
        logging.error(f"Failed to process file: {e}")
        sys.exit(1)

def read_chunks(json_path: str) -> List[Dict[str, Any]]:
    """
    Read chunks from JSON file.
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        List of chunk dictionaries
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('chunks', [])
    except Exception as e:
        logging.error(f"Failed to read chunks from {json_path}: {e}")
        raise

if __name__ == "__main__":
    main()
