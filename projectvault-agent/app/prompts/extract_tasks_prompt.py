"""Prompt for task extraction."""

EXTRACT_TASKS_PROMPT = """
Extract actionable tasks, requirements, errors, decisions, and concepts for a
lightweight project graph. Use only these node categories:
Project, File, Concept, Task, Error, Decision, Requirement.

Write every node label and description in Korean. Keep only the schema category
names and priority enum values in English.

Task priority must be one of HIGH, MEDIUM, LOW. Prefer HIGH for explicit
assignment requirements, submission blockers, failing code, or security risks.
Prefer concrete implementation tasks over vague study notes.
"""
