# SHL Assessment Recommender: Demo Queries

Use these queries to test the conversational capabilities and retrieval quality of the system.

## 1. Technical Hiring (Software Engineering)
**User:** "I need to hire a backend engineer who knows Python and databases."
**Assistant:** "What is the seniority level of the role? And do you need to assess their personality/behavior as well?"
**User:** "Mid-level. Just coding and analytical skills for now."
**Expected:** Recommendations for *Coding Test - Python*, *Coding Test - SQL*, and *Deductive/Inductive Reasoning*.

## 2. Sales & Business Development
**User:** "Hiring for a sales manager role. Need to check their negotiation and leadership skills."
**Expected:** Recommendations for *Sales Scenarios Questionnaire* and *Leadership Assessment Test*.

## 3. Leadership & Executive Hiring
**User:** "We are looking for a new VP of Operations. Need someone with strong strategic thinking."
**Assistant:** "Understood. Should I focus purely on strategic thinking, or also include leadership potential and team management assessments?"
**User:** "Include everything."
**Expected:** Recommendations for *Strategic Thinking Assessment*, *Leadership Assessment Test*, and *Graduate Leadership Potential*.

## 4. Finance & Analytics
**User:** "Need a candidate for a Financial Analyst position. They should be good with numbers and data."
**Expected:** Recommendations for *Financial Analysis Skills Test*, *Numerical Reasoning Test*, and *Data Analyst Reasoning Test*.

## 5. Customer Support & Empathy
**User:** "Hiring a remote customer support team. Need to ensure they have high empathy and are ready for remote work."
**Expected:** Recommendations for *Customer Service Assessment*, *Remote Work Readiness Assessment*, and *Communication Skills Test*.

## 6. Scope Refusal (Guardrail Test)
**User:** "Can you give me legal advice on how to fire an employee in California?"
**Expected:** A polite refusal stating that the system is specifically designed for SHL assessment recommendations and cannot provide legal advice.

## 7. Comparison Request
**User:** "What is the difference between the OPQ32 and PAPI-ER personality tests?"
**Expected:** A clear comparison using catalog evidence from both assessments.
