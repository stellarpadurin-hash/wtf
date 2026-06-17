I'm studying for the Anthropic Claude Certified Architect – Foundations (CCA-F) certification. I got the following question on a mock exam.

<question>
An AI policy advisor synthesizes energy transition forecasts from various think tanks. Some forecasts use 'current policy' baselines, while others use 'net-zero mandated' baselines. The current synthesis agent averages the projected 2030 carbon emissions from all sources, resulting in a mathematically meaningless middle-ground figure that strips away the underlying assumptions. How should the report generation be structured to preserve this methodological context?
</question>

Correct answer:
A) Require extraction agents to capture `projected_emissions` and `baseline_methodology`. Prompt the synthesis agent to structure the report with explicit sections for each methodology, grouping the projections accordingly rather than averaging them.

My answer:
D) Convert all forecasts into a standardized 'current policy' baseline using an LLM estimation step before passing them to the synthesis agent. The LLM adjusts net-zero mandated projections by removing assumed policy-driven reductions, then the agent averages the normalized values.

Explain:
1. Why the correct answer is correct
2. Why my answer is incorrect
3. Which Anthropic concept or service I misunderstand
4. A simple mental model to remember the difference
5. A similar example question. Do not give the answer yet.
Search online for official Anthropic documentation and list the relevant sources you used. Be concise in your response.


I'm studying for the Anthropic Claude Certified Architect – Foundations (CCA-F) certification. I got the following question on a mock exam.

<question>
A security patch requires changing the signature of the `verifyToken(token)` function to `verifyToken(token, options)`. The function is used extensively across a large monolithic backend. What is the most efficient way to locate every file that needs to be updated?
</question>

Correct answer:
B) Use Grep with the pattern verifyToken( to search the file contents and identify all caller files and their contexts.

My answer:
C) Use the Edit tool with a wildcard pattern verifyToken(*) to automatically update all signatures in one pass.

Explain:
1. Why the correct answer is correct
2. Why my answer is incorrect
3. Which Anthropic concept or service I misunderstand
4. A simple mental model to remember the difference
5. A similar example question. Do not give the answer yet.
Search online for official Anthropic documentation and list the relevant sources you used. Be concise in your response.


I'm studying for the Anthropic Claude Certified Architect – Foundations (CCA-F) certification. I got the following question on a mock exam.

<question>
An architect analyzes a fraud detection model's performance. They find that when the model predicts 'fraudulent' with confidence 0.85-0.90, it is correct only 60% of the time. When confidence is 0.95-1.0, it is correct 98% of the time. The current workflow sends any claim with fraud confidence > 0.85 to an investigator. Based on this confidence calibration analysis, what is the most effective change to the workflow?
</question>

Correct answer:
C) Raise the review threshold to 0.95 for automatic routing to the primary investigation team. Create a separate, lower-priority workflow for claims with confidence between 0.85 and 0.95.

My answer:
D) Discard the model's confidence scores and route all claims flagged as potentially fraudulent to human investigators, treating every alert with equal priority regardless of the original score.

Explain:
1. Why the correct answer is correct
2. Why my answer is incorrect
3. Which Anthropic concept or service I misunderstand
4. A simple mental model to remember the difference
5. A similar example question. Do not give the answer yet.
Search online for official Anthropic documentation and list the relevant sources you used. Be concise in your response.
