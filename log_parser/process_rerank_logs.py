#!/usr/bin/env python3
"""
Log file processing script
Extracts metadata from filenames and statistical information from log content
Generates CSV output sorted by model, dataset length, and concurrency level
"""

import os
import re
import csv
import sys
from datetime import datetime
from pathlib import Path


def extract_metadata_from_filename(filename):
    """
    Extract metadata from filename based on pattern:
    xeon_1000_bge-reranker-base_1_20250822_015049.log
    
    Returns: dict with hardware, dataset_length, model_name, concurrency_level
    """
    # Remove .log extension
    base_name = filename.rsplit('.', 1)[0]
    
    # Split by underscore
    parts = base_name.split('_')
    
    if len(parts) >= 5:
        hardware = parts[0]
        dataset_length = parts[1]
        
        # Find model name (everything between dataset_length and second-to-last part)
        model_parts = parts[2:-3]
        model_name = '_'.join(model_parts)
        
        concurrency_level = parts[-3]
        
        return {
            'hardware': hardware,
            'dataset_length': int(dataset_length) if dataset_length.isdigit() else dataset_length,
            'model_name': model_name,
            'concurrency_level': int(concurrency_level) if concurrency_level.isdigit() else concurrency_level,
            'filename': filename
        }
    else:
        return None


def extract_statistics_from_content(content):
    """
    Extract statistical information from log content based on the provided format
    """
    stats = {}
    
    # Define patterns to extract statistics
    patterns = {
        'total_concurrency': r'Total Concurrency:\s*(\d+)',
        'total_requests': r'Total Requests:\s*(\d+)',
        'total_test_time': r'Total Test time:\s*([\d.]+)',
        'avg_total_latency': r'avg total latency is\s*([\d.]+)\s*s',
        'p50_total_latency': r'P50 total latency is\s*([\d.]+)\s*s',
        'p90_total_latency': r'P90 total latency is\s*([\d.]+)\s*s',
        'p99_total_latency': r'P99 total latency is\s*([\d.]+)\s*s',
        'total_error_requests': r'Total error request is\s*(\d+)',
        'query_per_s': r'QPS is\s*(\d+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                stats[key] = float(match.group(1))
                # Convert integer values to int if they are whole numbers
                if key in ['total_concurrency', 'total_requests', 'total_error_requests']:
                    stats[key] = int(stats[key])
            except ValueError:
                stats[key] = match.group(1)
    
    # Calculate derived metrics
    if 'total_requests' in stats and 'total_test_time' in stats and stats['total_test_time'] > 0:
        stats['throughput_qps'] = stats['total_requests'] / stats['total_test_time']
    
    if 'total_requests' in stats and 'total_error_requests' in stats:
        stats['success_requests'] = stats['total_requests'] - stats['total_error_requests']
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['success_requests'] / stats['total_requests']) * 100
            stats['error_rate'] = (stats['total_error_requests'] / stats['total_requests']) * 100
    
    return stats


def process_log_file(file_path):
    """
    Process a single log file and extract all relevant information
    """
    filename = os.path.basename(file_path)
    
    # Extract metadata from filename
    metadata = extract_metadata_from_filename(filename)
    if not metadata:
        print(f"Skipping file with invalid format: {filename}")
        return None
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None
    
    # Extract statistics
    stats = extract_statistics_from_content(content)
    
    # Add file metadata
    file_stats = os.stat(file_path)
    metadata['file_size_bytes'] = file_stats.st_size
    metadata['last_modified'] = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
    
    # Combine metadata and statistics
    result = {**metadata, **stats}
    
    # Add raw content preview for debugging
    if not stats:
        result['raw_content'] = content.strip()[:100]
    
    return result


def process_directory(directory_path):
    """
    Process all log files in the given directory
    """
    log_files = []
    
    # Find all .log files
    for file_path in Path(directory_path).glob('*.log'):
        result = process_log_file(str(file_path))
        if result:
            log_files.append(result)
    
    return log_files


def save_to_csv(data, output_path):
    """
    Save processed data to CSV file with proper sorting
    """
    if not data:
        print("No data to save")
        return
    
    # Sort data: by model_name, then dataset_length, then concurrency_level
    sorted_data = sorted(data, key=lambda x: (
        x['model_name'],
        x['dataset_length'],
        x['concurrency_level']
    ))
    
    # Define standard column order
    primary_columns = [
        'model_name', 'dataset_length', 'concurrency_level', 'hardware', 'filename'
    ]
    
    stats_columns = [
        'total_concurrency', 'total_requests', 'total_test_time', 
        'avg_total_latency', 'p50_total_latency', 'p90_total_latency', 
        'p99_total_latency', 'total_error_requests', 'success_requests',
        'throughput_qps', 'success_rate', 'error_rate'
    ]
    
    # Add any additional columns found in data
    all_keys = set()
    for item in sorted_data:
        all_keys.update(item.keys())
    
    additional_columns = sorted(all_keys - set(primary_columns + stats_columns))
    headers = primary_columns + stats_columns + additional_columns
    
    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sorted_data)
    
    print(f"CSV file saved to: {output_path}")
    print(f"Total records: {len(sorted_data)}")


def print_summary(data):
    """
    Print summary information about processed data
    """
    if not data:
        return
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    # Group by model
    models = {}
    for item in data:
        model = item['model_name']
        if model not in models:
            models[model] = []
        models[model].append(item)
    
    print(f"Models found: {len(models)}")
    for model, items in models.items():
        dataset_lengths = set(item['dataset_length'] for item in items)
        concurrency_levels = set(item['concurrency_level'] for item in items)
        print(f"  {model}: {len(items)} files, dataset lengths: {sorted(dataset_lengths)}, concurrency: {sorted(concurrency_levels)}")
    
    # Overall stats
    dataset_lengths = set(item['dataset_length'] for item in data)
    total_files = len(data)
    
    print(f"\nDataset lengths: {sorted(dataset_lengths)}")
    print(f"Total log files processed: {total_files}")
    
    # Show first few records
    if data:
        print(f"\nFirst few records preview:")
        for i, item in enumerate(data[:3]):
            print(f"  {i+1}. {item['model_name']} - dataset:{item['dataset_length']} - concurrency:{item['concurrency_level']}")


def main():
    """
    Main function to handle command line arguments and process logs
    """
    if len(sys.argv) != 2:
        print("Usage: python process_logs.py <directory_path>")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        sys.exit(1)
    
    print(f"Processing log files in: {directory_path}")
    
    # Process all log files
    log_data = process_directory(directory_path)
    
    if not log_data:
        print("No log files found or processed successfully")
        sys.exit(1)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"processed_logs_{timestamp}.csv"
    
    # Save to CSV
    save_to_csv(log_data, output_path)
    
    # Print summary
    print_summary(log_data)


if __name__ == "__main__":
    main()
