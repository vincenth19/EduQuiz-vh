# MCQ Grading System

A simple system to process generated multiple-choice questions into structured data and simulate grading with timing analysis.

## Files

### 1. `process_mcq_data.py`
**Purpose**: Convert JSON quiz data to structured MCQ format and simulate random answer selection

**Functions**:
- Converts generated quiz strings to structured objects
- Matches passages from processed test data (with same random sampling as a3.py)
- Creates A/B/C/D labeled options
- Simulates random answer selection
- Saves structured data for grading

**Usage**:
```bash
python3 process_mcq_data.py
```

**Output Structure**:
```json
{
  "id": "A1_1",
  "passage": "Text passage from dataset...",
  "question": "Question text?",
  "options": [
    "A: First option",
    "B: Second option", 
    "C: Third option",
    "D: Fourth option"
  ],
  "answer": "A",
  "selected_option": "B"
}
```

### 2. `grade_mcqs.py`
**Purpose**: Grade MCQs by comparing correct answers with selected options, including timing analysis

**Functions**:
- Loads structured MCQ data
- Compares answer vs selected_option
- Calculates accuracy and grading speed
- Saves detailed grading results
- Provides timing benchmarks

**Usage**:
```bash
python3 grade_mcqs.py
```

**Features**:
- Batch processing of all structured files
- Detailed timing analysis (questions per second)
- Individual and overall accuracy statistics
- Speed demonstration mode

## Directory Structure

```
grading-system/
├── process_mcq_data.py     # Data processing script
├── grade_mcqs.py           # Grading script with timing
├── structured_data/        # Processed MCQ files
│   ├── a1_structured.json
│   ├── a2_structured.json
│   └── ...
└── grading_results/        # Grading results
    ├── a1_structured_grades.json
    ├── a2_structured_grades.json
    └── ...
```

## Sample Output

**Processing**: Converts 499 MCQs from 5 JSON files
**Grading Speed**: ~24,000 questions per second
**Random Accuracy**: ~20% (expected for random selection of 4 options)

## Key Features

1. **Consistent Sampling**: Uses same random seed (42) as a3.py for reproducible results
2. **Format Validation**: Robust parsing of quiz strings with error handling
3. **Speed Optimization**: Fast grading with detailed timing metrics
4. **Structured Output**: JSON format suitable for further analysis
5. **Batch Processing**: Handles multiple files automatically
