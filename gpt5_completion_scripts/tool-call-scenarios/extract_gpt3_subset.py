#!/usr/bin/env python3
"""
Extract the same 100-quiz subset from gpt3_output.json that matches the sampling in a3.py
"""

import json
import random
import os


def load_original_quizzes_with_indices(sample_size=100, random_seed=42):
    """Load original quizzes with their original indices - replicating a3.py logic"""
    
    # Construct path to processed_test.jsonl (same as a3.py)
    original_quiz_path = os.path.abspath(os.getcwd()).split('tool-call-scenarios')[0] + '../processed_data/gpt5/processed_test.jsonl'
    all_data = []
    
    # Load all data first with original indices
    with open(original_quiz_path, 'r') as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            quiz = data['completion'].split("\n###")[0].replace("\n", " ").strip()
            all_data.append({
                'original_index': idx,  # Store the original index (0-based)
                'quiz': quiz,
                'prompt': data.get('prompt', ''),
                'original_data': data
            })
    
    print(f"Loaded {len(all_data)} total quizzes from dataset")
    
    # Sample using the same logic as a3.py
    if sample_size and sample_size < len(all_data):
        random.seed(random_seed)
        sampled_data = random.sample(all_data, sample_size)
        print(f"Randomly sampled {sample_size} quizzes (seed={random_seed})")
        
        # Sort by original index to maintain order
        sampled_data.sort(key=lambda x: x['original_index'])
        return sampled_data
    else:
        print(f"Using all {len(all_data)} quizzes")
        return all_data


def extract_gpt3_subset():
    """Extract the corresponding subset from gpt3_output.json"""
    
    # Get the sampled data with original indices
    sampled_data = load_original_quizzes_with_indices(sample_size=100, random_seed=42)
    
    # Load the full gpt3_output.json
    gpt3_output_path = "../../generated_data_gpt5/gpt3_output.json"
    
    with open(gpt3_output_path, 'r') as f:
        gpt3_full_output = json.load(f)
    
    print(f"Loaded {len(gpt3_full_output)} entries from gpt3_output.json")
    
    # Create mapping from original indices to gpt3 results
    # Note: gpt3_output.json uses 1-based indexing, original indices are 0-based
    sampled_gpt3_output = {}
    found_indices = []
    missing_indices = []
    
    for i, sample in enumerate(sampled_data):
        original_idx = sample['original_index']
        gpt3_key = str(original_idx + 1)  # Convert to 1-based indexing
        
        if gpt3_key in gpt3_full_output:
            sampled_gpt3_output[str(i + 1)] = gpt3_full_output[gpt3_key]  # Use 1-based for consistency
            found_indices.append(original_idx)
        else:
            missing_indices.append(original_idx)
            print(f"Warning: Missing gpt3 result for original index {original_idx} (gpt3 key: {gpt3_key})")
    
    print(f"\nExtraction Summary:")
    print(f"- Sampled indices: {len(sampled_data)}")
    print(f"- Found in gpt3_output.json: {len(found_indices)}")
    print(f"- Missing from gpt3_output.json: {len(missing_indices)}")
    
    if missing_indices:
        print(f"Missing indices: {missing_indices}")
    
    # Save the extracted subset
    output_path = "../../generated_data_gpt5/gpt3_output_subset.json"
    with open(output_path, 'w') as f:
        json.dump(sampled_gpt3_output, f, indent=2)
    
    print(f"\nSaved extracted subset to: {os.path.abspath(output_path)}")
    
    # Create a mapping file for reference
    mapping = {}
    for i, sample in enumerate(sampled_data):
        mapping[str(i + 1)] = {
            'original_index': sample['original_index'],
            'gpt3_key': str(sample['original_index'] + 1),
            'prompt_preview': sample['prompt'][:100] + "..." if len(sample['prompt']) > 100 else sample['prompt']
        }
    
    mapping_path = "../../generated_data_gpt5/gpt3_subset_mapping.json"
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Saved index mapping to: {os.path.abspath(mapping_path)}")
    
    # Show first few entries for verification
    print(f"\nFirst 5 entries in extracted subset:")
    for i in range(min(5, len(sampled_gpt3_output))):
        key = str(i + 1)
        if key in sampled_gpt3_output:
            quiz_preview = sampled_gpt3_output[key][:100] + "..." if len(sampled_gpt3_output[key]) > 100 else sampled_gpt3_output[key]
            original_idx = sampled_data[i]['original_index']
            print(f"  {key}: (orig_idx:{original_idx}) {quiz_preview}")
    
    return sampled_gpt3_output, sampled_data


if __name__ == "__main__":
    print("Extracting GPT-3 subset matching a3.py sampling...")
    extract_gpt3_subset()
