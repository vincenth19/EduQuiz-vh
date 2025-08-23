# Generator User Prompt Template

## For Single-Agent Scenarios (A1, A2)
```
Here are some examples of good quiz generation:

{k_shot_examples}

---

Generate a quiz for this passage:

{passage}
```

## For Two-Agent Scenarios - First Round (A3-SS, A3-SR, A3-RS, A3-RR)
```
Here are some examples:

{k_shot_examples}

---

Generate a quiz for this passage:

{passage}
```

## For Two-Agent Scenarios - Revision Rounds
```
Here are some examples:

{k_shot_examples}

---

Generate a quiz for this passage:

{passage}

Previous feedback: {feedback}
Please revise accordingly.
```
