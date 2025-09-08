import json
import random
import os
from typing import List, Dict, Any

def load_passages_with_sampling(sample_size=100, random_seed=42):
    """Load passages from processed_test.jsonl with same sampling as a3.py"""
    
    processed_test_path = '../processed_data/gpt5/processed_test.jsonl'
    all_data = []
    
    with open(processed_test_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            all_data.append({
                'passage': data['prompt'].split('\n###\n')[0].strip(),
                'prompt': data.get('prompt', ''),
                'original_data': data
            })
    
    print(f"Loaded {len(all_data)} total passages from dataset")
    
    if sample_size and sample_size < len(all_data):
        random.seed(random_seed)
        sampled_data = random.sample(all_data, sample_size)
        print(f"Randomly sampled {sample_size} passages (seed={random_seed})")
        return sampled_data
    else:
        print(f"Using all {len(all_data)} passages")
        return all_data

def parse_quiz_string(quiz_string: str) -> Dict[str, Any]:
    """Parse quiz string to extract question, true answer, and false answers"""
    
    if not quiz_string or 'Question:' not in quiz_string:
        return None
    
    try:
        parts = quiz_string.split('Question:')[1]
        
        if 'True answer:' not in parts:
            return None
            
        question = parts.split('True answer:')[0].strip()
        
        remaining = parts.split('True answer:')[1]
        if 'False answer:' not in remaining:
            return None
            
        true_answer = remaining.split('False answer:')[0].strip()
        
        false_answers = []
        false_parts = remaining.split('False answer:')[1:]
        
        for false_part in false_parts:
            false_answer = false_part.split('False answer:')[0].strip()
            if false_answer:
                false_answers.append(false_answer)
        
        return {
            'question': question,
            'true_answer': true_answer,
            'false_answers': false_answers
        }
    
    except Exception as e:
        print(f"Error parsing quiz string: {e}")
        return None

def convert_to_structured_mcq(passages: List[Dict], generated_data: Dict[str, str]) -> List[Dict[str, Any]]:
    """Convert generated quiz data to structured MCQ format"""
    
    structured_mcqs = []
    
    for idx, (quiz_id, quiz_string) in enumerate(generated_data.items()):
        if idx >= len(passages):
            print(f"Warning: More quizzes than passages, skipping {quiz_id}")
            continue
            
        parsed_quiz = parse_quiz_string(quiz_string)
        if not parsed_quiz:
            print(f"Warning: Could not parse quiz {quiz_id}")
            continue
        
        all_options = [parsed_quiz['true_answer']] + parsed_quiz['false_answers']
        
        random.shuffle(all_options)
        
        correct_answer_index = all_options.index(parsed_quiz['true_answer'])
        answer_labels = ['A', 'B', 'C', 'D']
        correct_answer = answer_labels[correct_answer_index]
        
        options_with_labels = [f"{label}: {option}" for label, option in zip(answer_labels, all_options)]
        
        mcq_object = {
            'id': quiz_id,
            'passage': passages[idx]['passage'],
            'question': parsed_quiz['question'],
            'options': options_with_labels,
            'answer': correct_answer,
            'selected_option': ''
        }
        
        structured_mcqs.append(mcq_object)
    
    return structured_mcqs

def simulate_random_answers(mcqs: List[Dict[str, Any]], random_seed=42) -> List[Dict[str, Any]]:
    """Simulate random answer selection for each MCQ"""
    
    random.seed(random_seed)
    answer_choices = ['A', 'B', 'C', 'D']
    
    for mcq in mcqs:
        mcq['selected_option'] = random.choice(answer_choices)
    
    return mcqs

def process_json_file(json_file_path: str, output_dir: str = 'structured_data'):
    """Process a single JSON file and save structured MCQ data"""
    
    print(f"\nProcessing {json_file_path}...")
    
    passages = load_passages_with_sampling(sample_size=100, random_seed=42)
    
    with open(json_file_path, 'r') as f:
        generated_data = json.load(f)
    
    structured_mcqs = convert_to_structured_mcq(passages, generated_data)
    
    structured_mcqs = simulate_random_answers(structured_mcqs)
    
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = os.path.splitext(os.path.basename(json_file_path))[0]
    output_path = os.path.join(output_dir, f"{base_filename}_structured.json")
    
    with open(output_path, 'w') as f:
        json.dump(structured_mcqs, f, indent=2)
    
    print(f"Successfully processed {len(structured_mcqs)} MCQs")
    print(f"Saved to: {output_path}")
    
    return structured_mcqs

def process_all_json_files(input_dir: str = '../generated_data_gpt5', output_dir: str = 'structured_data'):
    """Process all JSON files in the input directory"""
    
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json') and not f.endswith('.bkp')]
    
    print(f"Found {len(json_files)} JSON files to process:")
    for f in json_files:
        print(f"  - {f}")
    
    all_results = {}
    
    for json_file in json_files:
        json_path = os.path.join(input_dir, json_file)
        try:
            structured_mcqs = process_json_file(json_path, output_dir)
            all_results[json_file] = structured_mcqs
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            all_results[json_file] = []
    
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    total_mcqs = sum(len(mcqs) for mcqs in all_results.values())
    print(f"Total MCQs processed: {total_mcqs}")
    print(f"Files saved in: {os.path.abspath(output_dir)}")
    
    return all_results

def load_structured_mcqs(file_path: str) -> List[Dict[str, Any]]:
    """Load structured MCQ data from file (for grading script)"""
    with open(file_path, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    process_all_json_files()
