import time
import json
import os
from typing import List, Dict, Any, Tuple
from process_mcq_data import load_structured_mcqs

def grade_single_mcq(mcq: Dict[str, Any]) -> Dict[str, Any]:
    """Grade a single MCQ by comparing answer with selected_option"""
    
    is_correct = mcq['answer'] == mcq['selected_option']
    
    result = {
        'id': mcq['id'],
        'question': mcq['question'],
        'correct_answer': mcq['answer'],
        'selected_answer': mcq['selected_option'],
        'is_correct': is_correct,
        'score': 1 if is_correct else 0
    }
    
    return result

def grade_mcq_list(mcqs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Grade a list of MCQs and return results with statistics"""
    
    start_time = time.time()
    
    grading_results = []
    
    for mcq in mcqs:
        if not mcq.get('selected_option'):
            print(f"Warning: No selected option for MCQ {mcq.get('id', 'unknown')}")
            continue
            
        result = grade_single_mcq(mcq)
        grading_results.append(result)
    
    end_time = time.time()
    grading_time = end_time - start_time
    
    total_questions = len(grading_results)
    correct_answers = sum(1 for result in grading_results if result['is_correct'])
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    statistics = {
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'wrong_answers': total_questions - correct_answers,
        'accuracy_percentage': round(accuracy, 2),
        'grading_time_seconds': round(grading_time, 4),
        'questions_per_second': round(total_questions / grading_time, 2) if grading_time > 0 else 0
    }
    
    return grading_results, statistics

def grade_file(structured_mcq_file: str, output_dir: str = 'grading_results') -> Dict[str, Any]:
    """Grade MCQs from a structured file and save results"""
    
    print(f"\nGrading MCQs from: {structured_mcq_file}")
    
    mcqs = load_structured_mcqs(structured_mcq_file)
    print(f"Loaded {len(mcqs)} MCQs for grading")
    
    grading_results, statistics = grade_mcq_list(mcqs)
    
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = os.path.splitext(os.path.basename(structured_mcq_file))[0]
    results_filename = f"{base_filename}_grades.json"
    results_path = os.path.join(output_dir, results_filename)
    
    output_data = {
        'statistics': statistics,
        'detailed_results': grading_results
    }
    
    with open(results_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"GRADING RESULTS FOR: {base_filename}")
    print(f"{'='*50}")
    print(f"Total Questions: {statistics['total_questions']}")
    print(f"Correct Answers: {statistics['correct_answers']}")
    print(f"Wrong Answers: {statistics['wrong_answers']}")
    print(f"Accuracy: {statistics['accuracy_percentage']}%")
    print(f"Grading Time: {statistics['grading_time_seconds']} seconds")
    print(f"Speed: {statistics['questions_per_second']} questions/second")
    print(f"Results saved to: {results_path}")
    
    return output_data

def grade_all_structured_files(structured_dir: str = 'structured_data', output_dir: str = 'grading_results'):
    """Grade all structured MCQ files in directory"""
    
    if not os.path.exists(structured_dir):
        print(f"Error: Directory {structured_dir} does not exist")
        return
    
    structured_files = [f for f in os.listdir(structured_dir) if f.endswith('_structured.json')]
    
    if not structured_files:
        print(f"No structured MCQ files found in {structured_dir}")
        return
    
    print(f"Found {len(structured_files)} structured MCQ files to grade:")
    for f in structured_files:
        print(f"  - {f}")
    
    all_results = {}
    total_start_time = time.time()
    
    for structured_file in structured_files:
        file_path = os.path.join(structured_dir, structured_file)
        try:
            result = grade_file(file_path, output_dir)
            all_results[structured_file] = result
        except Exception as e:
            print(f"Error grading {structured_file}: {e}")
            all_results[structured_file] = None
    
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    print(f"\n{'='*60}")
    print(f"BATCH GRADING COMPLETE")
    print(f"{'='*60}")
    
    total_questions_all = sum(
        result['statistics']['total_questions'] 
        for result in all_results.values() 
        if result is not None
    )
    
    total_correct_all = sum(
        result['statistics']['correct_answers'] 
        for result in all_results.values() 
        if result is not None
    )
    
    overall_accuracy = (total_correct_all / total_questions_all * 100) if total_questions_all > 0 else 0
    
    print(f"Total Files Processed: {len([r for r in all_results.values() if r is not None])}")
    print(f"Total Questions Graded: {total_questions_all}")
    print(f"Total Correct: {total_correct_all}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print(f"Total Grading Time: {total_time:.4f} seconds")
    print(f"Average Speed: {total_questions_all / total_time:.2f} questions/second")
    print(f"Results directory: {os.path.abspath(output_dir)}")
    
    return all_results

def demonstrate_grading_speed(num_questions: int = 1000):
    """Demonstrate grading speed with sample data"""
    
    print(f"\n{'='*50}")
    print(f"GRADING SPEED DEMONSTRATION")
    print(f"{'='*50}")
    
    sample_mcqs = []
    for i in range(num_questions):
        mcq = {
            'id': f'TEST_{i+1}',
            'question': f'Sample question {i+1}?',
            'answer': 'A',
            'selected_option': 'A' if i % 4 == 0 else 'B'  # 25% correct
        }
        sample_mcqs.append(mcq)
    
    print(f"Created {num_questions} sample MCQs for speed test")
    
    grading_results, statistics = grade_mcq_list(sample_mcqs)
    
    print(f"Grading Speed Results:")
    print(f"  - Questions graded: {statistics['total_questions']}")
    print(f"  - Time taken: {statistics['grading_time_seconds']} seconds")
    print(f"  - Speed: {statistics['questions_per_second']} questions/second")
    print(f"  - Accuracy: {statistics['accuracy_percentage']}%")
    
    return statistics

if __name__ == "__main__":
    
    print("MCQ Grading System")
    print("=" * 60)
    
    # Check if structured data exists
    if os.path.exists('structured_data'):
        print("\nGrading structured MCQ files...")
        grade_all_structured_files()
    else:
        print("\nNo structured data found. Run process_mcq_data.py first.")
        print("Demonstrating grading speed with sample data...")
        demonstrate_grading_speed(1000)
