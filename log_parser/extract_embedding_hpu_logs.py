#!/usr/bin/env python3
"""
Extract information from HPU log files and save to CSV.
"""

import os
import re
import csv
from glob import glob


def parse_log_filename(filename):
    """Parse log filename to extract model, data file, and concurrency."""
    basename = os.path.basename(filename)
    if not basename.startswith('hpu_') or not basename.endswith('.log'):
        return None
    
    # Remove prefix and suffix
    parts = basename[4:-4].split('_')
    if len(parts) < 5:
        return None
    
    # Format: model_datafile_concurrency_timestamp
    # Find the parts: model can contain underscores, data file is 21_512, concurrency is number
    model_parts = []
    i = 0
    while i < len(parts) and not (parts[i].isdigit() and i + 1 < len(parts) and parts[i+1].isdigit()):
        model_parts.append(parts[i])
        i += 1
    
    if i + 2 >= len(parts):
        return None
    
    model = '_'.join(model_parts)
    data_file = f"{parts[i]}_{parts[i+1]}"
    concurrency = parts[i+2]
    
    return {
        'model': model,
        'data_file': data_file,
        'concurrency': concurrency
    }


def extract_log_data(filepath):
    """Extract metrics from log file content."""
    data = {
        'qps': None,
        'total_time': None,
        'avg_time': None,
        'median_time': None,
        'p90_time': None,
        'p95_time': None
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract QPS
        qps_match = re.search(r'QPS:\s*([\d.]+)\s*请求/秒', content)
        if qps_match:
            data['qps'] = float(qps_match.group(1))
        
        # Extract total time
        total_time_match = re.search(r'总耗时:\s*([\d.]+)\s*秒', content)
        if total_time_match:
            data['total_time'] = float(total_time_match.group(1))
        
        # Extract average time
        avg_match = re.search(r'平均值:\s*([\d.]+)s', content)
        if avg_match:
            data['avg_time'] = float(avg_match.group(1))
        
        # Extract median time
        median_match = re.search(r'中位数:\s*([\d.]+)s', content)
        if median_match:
            data['median_time'] = float(median_match.group(1))
        
        # Extract P90 time
        p90_match = re.search(r'P90:\s*([\d.]+)s', content)
        if p90_match:
            data['p90_time'] = float(p90_match.group(1))
        
        # Extract P95 time
        p95_match = re.search(r'P95:\s*([\d.]+)s', content)
        if p95_match:
            data['p95_time'] = float(p95_match.group(1))
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return data


def process_log_directory(directory='.'):
    """Process all log files in the directory."""
    log_files = glob(os.path.join(directory, 'hpu_*.log'))
    
    results = []
    
    for log_file in log_files:
        filename_data = parse_log_filename(log_file)
        if not filename_data:
            continue
            
        log_data = extract_log_data(log_file)
        
        # Combine filename and log data
        result = {
            'filename': os.path.basename(log_file),
            'model': filename_data['model'],
            'data_file': filename_data['data_file'],
            'concurrency': filename_data['concurrency'],
            'qps': log_data['qps'],
            'total_time': log_data['total_time'],
            'avg_time': log_data['avg_time'],
            'median_time': log_data['median_time'],
            'p90_time': log_data['p90_time'],
            'p95_time': log_data['p95_time']
        }
        
        results.append(result)
    
    return results


def save_to_csv(results, output_file='1_hpu_results.csv'):
    """Save results to CSV file, grouped by model and sorted by concurrency."""
    if not results:
        print("No results to save")
        return
    
    # Sort results by model, then by data_file, then by concurrency (ascending)
    sorted_results = sorted(results, key=lambda x: (x['model'], x['data_file'], int(x['concurrency'])))
    
    fieldnames = [
        'filename', 'model', 'data_file', 'concurrency', 
        'qps', 'total_time', 'avg_time', 'median_time', 
        'p90_time', 'p95_time'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Group by model and write with separator
        current_model = None
        for result in sorted_results:
            if result['model'] != current_model:
                current_model = result['model']
                # Write separator row (empty row for visual grouping)
                writer.writerow({field: '' for field in fieldnames})
            writer.writerow(result)
    
    print(f"Results saved to {output_file}")
    
    # Print grouped summary
    print("\nGrouped Summary:")
    current_model = None
    for result in sorted_results:
        if result['model'] != current_model:
            current_model = result['model']
            print(f"\n=== {current_model} ===")
        print(f"  Concurrency {result['concurrency']}: QPS={result['qps']}")


def save_grouped_csv(results, output_file='hpu_results_grouped.csv'):
    """Save results to CSV file with separate sheets for each model (separate files)."""
    if not results:
        print("No results to save")
        return
    
    # Group by model
    models = {}
    for result in results:
        model = result['model']
        if model not in models:
            models[model] = []
        models[model].append(result)
    
    # Create separate CSV files for each model
    for model, model_results in models.items():
        # Sort by data_file first, then by concurrency ascending
        model_results.sort(key=lambda x: (x['data_file'], int(x['concurrency'])))
        
        safe_model_name = model.replace('/', '_').replace(' ', '_')
        filename = f"hpu_results_{safe_model_name}.csv"
        
        fieldnames = [
            'filename', 'data_file', 'concurrency', 
            'qps', 'total_time', 'avg_time', 'median_time', 
            'p90_time', 'p95_time'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in model_results:
                # Remove model column since it's in filename
                row = {k: v for k, v in result.items() if k != 'model'}
                writer.writerow(row)
        
        print(f"Model results saved to {filename}")
    
    return models


def main():
    """Main function."""
    directory = '.'  # Current directory
    
    print("Processing HPU log files...")
    results = process_log_directory(directory)
    
    if results:
        print(f"Processed {len(results)} log files")
        
        # Save grouped by model and sorted
        save_to_csv(results)
        
        # Save separate files for each model
        models = save_grouped_csv(results)
        
    else:
        print("No valid log files found")


if __name__ == '__main__':
    main()
