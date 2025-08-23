# Evaluator User Prompt Template

## Standard Template
```
Passage: {passage}

Generated Quiz:
{quiz_text}

Evaluate this quiz and respond with either "accept" or "revise: [feedback]".
```

## Reasoning Model Template (for A3-SR, A3-RR)
```
Passage: {passage}

Generated Quiz:
{quiz_text}

Evaluate this quiz thoroughly and respond with either "accept" or "revise: [detailed feedback]".
```
