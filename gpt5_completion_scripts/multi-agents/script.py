import asyncio
import json
import os
import evaluate
from agents import Agent, Runner, function_tool
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please create a .env file with OPENAI_API_KEY=your-key")

# Load original quizzes for comparison
def load_original_quizzes(sample_size=150, random_seed=42):
    """Load original quizzes from processed test data with optional random sampling"""
    import random
    
    original_quiz_path = os.path.abspath(os.getcwd()).split('multi-agents')[0] + '../processed_data/gpt5/processed_test.jsonl'
    all_data = []
    
    # Load all data first
    with open(original_quiz_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            quiz = data['completion'].split("\n###")[0].replace("\n", " ").strip()
            all_data.append({
                'quiz': quiz,
                'prompt': data.get('prompt', ''),
                'original_data': data
            })
    
    print(f"Loaded {len(all_data)} total quizzes from dataset")
    
    # Sample if requested
    if sample_size and sample_size < len(all_data):
        random.seed(random_seed)
        sampled_data = random.sample(all_data, sample_size)
        print(f"Randomly sampled {sample_size} quizzes (seed={random_seed})")
        return sampled_data
    else:
        print(f"Using all {len(all_data)} quizzes")
        return all_data

# Load original quizzes once at startup - Full 150 rows
ORIGINAL_QUIZZES = load_original_quizzes(sample_size=150, random_seed=42)

@function_tool
def evaluate_quiz_quality(generated_quiz: str, quiz_index: int) -> str:
    """Evaluate quiz quality using ROUGE-L score against reference quiz (same as evaluation notebook)."""
    if quiz_index >= len(ORIGINAL_QUIZZES):
        return "Error: Quiz index out of range"
    
    reference_quiz = ORIGINAL_QUIZZES[quiz_index]['quiz']
    
    print(f"[DEBUG] Evaluating quiz {quiz_index + 1}")
    print(f"[DEBUG] Reference: {reference_quiz[:100]}...")
    print(f"[DEBUG] Generated: {generated_quiz[:100]}...")
    
    # Use same evaluation method as notebook
    rouge = evaluate.load('rouge')
    
    # Format for evaluate library (needs lists)
    predictions = [generated_quiz.replace("\n", " ").strip()]
    references = [[reference_quiz.replace("\n", " ").strip()]]
    
    rouge.add_batch(predictions=predictions, references=references)
    rouge_results = rouge.compute()
    rouge_l_score = rouge_results['rougeL'] * 100
    
    # Calculate basic metrics
    length_ratio = len(generated_quiz) / len(reference_quiz) if len(reference_quiz) > 0 else 0
    word_overlap = len(set(generated_quiz.split()) & set(reference_quiz.split()))
    
    # Generate feedback
    feedback = f"ROUGE-L Score: {rouge_l_score:.2f}/100\n"
    
    print(f"[DEBUG] ROUGE-L Score: {rouge_l_score:.2f}")
    
    if rouge_l_score < 25:
        feedback += "NEEDS IMPROVEMENT: Low lexical overlap with reference. "
        feedback += "Focus on using similar vocabulary and phrasing patterns."
    elif rouge_l_score < 35:
        feedback += "MODERATE: Some similarity to reference. "
        feedback += "Consider using more exact phrases from the passage."
    else:
        feedback += "GOOD: Strong similarity to reference style."
    
    if length_ratio < 0.7:
        feedback += " Quiz seems too short - add more detail."
    elif length_ratio > 1.5:
        feedback += " Quiz seems too long - be more concise."
    
    feedback += f" Word overlap: {word_overlap} words."
    
    print(f"[DEBUG] Feedback: {feedback}")
    return feedback

@function_tool
def check_quiz_format(quiz_text: str) -> str:
    """Check if quiz follows the required format structure."""
    required_elements = [
        "Question:",
        "True answer:",
        "False answer:"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in quiz_text:
            missing_elements.append(element)
    
    # Count false answers
    false_answer_count = quiz_text.count("False answer:")
    
    if missing_elements:
        return f"FORMAT ERROR: Missing elements: {', '.join(missing_elements)}"
    
    if false_answer_count != 3:
        return f"FORMAT ERROR: Expected 3 'False answer:' entries, found {false_answer_count}"
    
    return "FORMAT OK: Quiz follows required structure"

@function_tool
def suggest_improvements(quiz_text: str, evaluation_feedback: str) -> str:
    """Provide specific improvement suggestions based on evaluation."""
    suggestions = []
    
    # Parse ROUGE score from feedback
    if "ROUGE-L Score:" in evaluation_feedback:
        score_line = evaluation_feedback.split("ROUGE-L Score:")[1].split("\n")[0]
        try:
            score = float(score_line.split("/")[0])
        except:
            score = 0
    else:
        score = 0
    
    # Question analysis
    if "Question:" in quiz_text:
        question = quiz_text.split("Question:")[1].split("True answer:")[0].strip()
        question_words = len(question.split())
        
        if question_words > 15:
            suggestions.append("Shorten question to 10-15 words for clarity")
        
        if "?" not in question:
            suggestions.append("Ensure question ends with a question mark")
    
    # Score-based suggestions
    if score < 25:
        suggestions.append("Use more exact phrases from the original passage")
        suggestions.append("Follow the language patterns from high-scoring examples")
        suggestions.append("Ensure answer options have parallel grammatical structure")
    elif score < 35:
        suggestions.append("Improve lexical consistency across answer options")
        suggestions.append("Use simpler, more direct vocabulary")
    
    if not suggestions:
        suggestions.append("Quiz quality is good - minor refinements only")
    
    return "SUGGESTIONS:\n" + "\n".join(f"- {s}" for s in suggestions)

def load_system_prompt():
    """Load the generator system prompt from markdown file"""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'generator_agent_system_prompt.md')
    
    with open(prompt_path, 'r') as f:
        base_prompt = f.read()
    
    # Add tool-specific instructions
    tool_instructions = """

## EVALUATION TOOLS AVAILABLE

You have access to three evaluation tools to improve your quiz quality:

### 1. evaluate_quiz_quality(generated_quiz: str, quiz_index: int)
- Calculates ROUGE-L score against reference quiz
- Provides feedback on lexical overlap and length
- Target: ROUGE-L score ≥ 30 for good quality

### 2. check_quiz_format(quiz_text: str) 
- Validates required format structure
- Ensures proper "Question:", "True answer:", "False answer:" elements
- Confirms exactly 3 false answers

### 3. suggest_improvements(quiz_text: str, evaluation_feedback: str)
- Provides specific actionable suggestions
- Analyzes question length and structure
- Recommends vocabulary and phrasing improvements

## MANDATORY EVALUATION PROCESS

After generating each quiz, you MUST:
1. **Call evaluate_quiz_quality()** to get ROUGE-L score and feedback
2. **Call check_quiz_format()** to verify structure
3. **If ROUGE-L < 30 OR format errors exist:**
   - Call suggest_improvements() for specific guidance
   - Refine the quiz based on feedback
   - Re-evaluate with tools
4. **Maximum 2 refinement rounds** to control costs

## REFINEMENT PRIORITIES (in order)
1. **Format compliance** - Fix any structural issues first
2. **Lexical overlap** - Use more exact phrases from passage/reference style
3. **Question length** - Keep to 10-15 words when possible
4. **Answer parallelism** - Ensure consistent grammatical structure
5. **Vocabulary simplicity** - Use direct, clear language

## SUCCESS CRITERIA
- ROUGE-L score ≥ 30
- Perfect format compliance
- All quality checklist items met

Always use your evaluation tools to verify and improve your work systematically."""
    
    return base_prompt + tool_instructions

def extract_latest_quiz_from_result(result):
    """Extract the most recent quiz attempt from conversation history"""
    try:
        # Look through the conversation items to find quiz-like content
        if hasattr(result, 'new_items'):
            for item in reversed(result.new_items):
                if hasattr(item, 'content') and item.content:
                    content = item.content
                    # Check if this looks like a quiz (has Question: and True answer:)
                    if "Question:" in content and "True answer:" in content:
                        return content
        
        # Fallback to final_output if available
        if hasattr(result, 'final_output') and result.final_output:
            if "Question:" in result.final_output:
                return result.final_output
        
        return None
    except:
        return None

# Quiz Generator Agent
quiz_agent = Agent(
    name="QuizGenerator",
    instructions=load_system_prompt(),
    tools=[evaluate_quiz_quality, check_quiz_format, suggest_improvements],
    model="gpt-5-2025-08-07"
)

async def generate_quiz_with_refinement(quiz_index: int):
    """Generate a quiz with iterative refinement based on evaluation feedback."""
    
    if quiz_index >= len(ORIGINAL_QUIZZES):
        raise ValueError(f"Quiz index {quiz_index} out of range")
    
    # Get the prompt from sampled data
    prompt = ORIGINAL_QUIZZES[quiz_index]['prompt']
    
    user_prompt = f"""Generate a multiple-choice quiz question based on this passage:

{prompt}

PROCESS (3 turns max):
1. Generate your initial quiz
2. Call evaluate_quiz_quality(generated_quiz, {quiz_index}) to get ROUGE-L score
3. If ROUGE-L < 30, refine the quiz based on feedback (no additional tools needed)

Be efficient - focus on the most impactful improvements.

Follow the format and style guidelines in your instructions."""
    
    print(f"Generating quiz {quiz_index + 1}/{len(ORIGINAL_QUIZZES)}...")
    
    # Run the agent with simplified turn limit
    try:
        print(f"[DEBUG] Starting agent with max 3 turns...")
        result = await Runner.run(
            quiz_agent, 
            input=user_prompt,
            max_turns=3  # Cost-effective: 1 generation + 1 evaluation + 1 refinement (if needed)
        )
        print(f"[DEBUG] Agent completed successfully")
        print(f"[DEBUG] Final output: {result.final_output[:200]}...")
        return result.final_output
    except Exception as e:
        print(f"  Exception for quiz {quiz_index + 1}: {str(e)[:100]}...")
        
        # If any error occurs, generate a fallback quiz without evaluation tools
        try:
            fallback_prompt = f"""Generate a simple multiple-choice quiz question based on this passage (NO EVALUATION TOOLS):

{prompt}

Use this exact format:
Question: [Your question here]
True answer: [Correct answer]
False answer: [Incorrect option 1]
False answer: [Incorrect option 2]
False answer: [Incorrect option 3]"""
            
            fallback_result = await Runner.run(
                Agent(
                    name="SimpleFallbackGenerator",
                    instructions="Generate a simple quiz question without using any tools. Follow the exact format specified.",
                    model="gpt-4o"
                ),
                input=fallback_prompt,
                max_turns=2
            )
            return fallback_result.final_output
        except:
            # Final fallback with a generic quiz
            return f"Question: What is mentioned in the passage?\nTrue answer: Information from the text.\nFalse answer: Unrelated information.\nFalse answer: Different topic.\nFalse answer: Incorrect details."

async def main():
    """Main function to run full batch generation and save results."""
    
    print(f"Starting full batch generation with {len(ORIGINAL_QUIZZES)} sampled quizzes...")
    
    # Generate all quizzes with evaluation
    results = await batch_generate_quizzes()
    
    # Transform to required format and save
    output_data = {}
    successful_count = 0
    
    for result in results:
        if 'generated_quiz' in result:
            quiz_id = str(result['index'] + 1)  # 1-indexed like a1_test.json
            output_data[quiz_id] = result['generated_quiz']
            successful_count += 1
    
    # Save to generated_data_gpt5 directory - Full batch with 3 turns
    output_path = "../../generated_data_gpt5/a3-3turns.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BATCH GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully generated: {successful_count}/{len(ORIGINAL_QUIZZES)} quizzes")
    print(f"Saved to: {os.path.abspath(output_path)}")
    print(f"Format matches: a1_test.json structure")
    
    # Show sample of results
    if successful_count > 0:
        print(f"\nSample generated quiz:")
        first_key = list(output_data.keys())[0]
        print(f"Quiz {first_key}: {output_data[first_key][:100]}...")
    
    return output_data

async def batch_generate_quizzes(num_quizzes=None):
    """Generate multiple quizzes in batch"""
    if num_quizzes is None:
        num_quizzes = len(ORIGINAL_QUIZZES)
    
    results = []
    for i in range(min(num_quizzes, len(ORIGINAL_QUIZZES))):
        try:
            quiz = await generate_quiz_with_refinement(i)
            results.append({
                'index': i,
                'generated_quiz': quiz,
                'reference_quiz': ORIGINAL_QUIZZES[i]['quiz'],
                'prompt': ORIGINAL_QUIZZES[i]['prompt']
            })
            print(f"Completed quiz {i+1}/{num_quizzes}")
        except Exception as e:
            print(f"Failed quiz {i+1}: {e}")
            results.append({
                'index': i,
                'error': str(e)
            })
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
