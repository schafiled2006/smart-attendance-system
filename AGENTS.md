# AGENTS.md

Instructions for the coding agent working on this project (OpenCode reads this file automatically).
This file is authoritative. If `.clinerules` exists, it must say the same thing.
Do NOT regenerate, overwrite or "improve" this file with /init or any generator. Edit it only when I ask.

## 1. Start of every session
1. Read `PROJECT_CONTEXT.md` completely.
2. Read this file completely.
3. Read `progress/current_status.md` and continue from where it stopped.
4. If any of them is missing, tell me and stop. Do not recreate it silently.
5. This is a backend-only project. Ignore `SMART_ATTENDANCE_FRONTEND_SPEC.md`, `.claude/` and `blobs/`.

## 2. Permanent rules
- Do only ONE stage per session.
- A stage is complete only when its tests pass with pytest. Show the real test output. If tests were skipped, say so and do not call the stage fully verified.
- Do not change technologies, folder structure, database schema or function signatures without asking me first.
- Touch earlier stages' files only to fix bugs, and record each such change under "Known bugs" in `progress/current_status.md`.
- Use only free and open-source tools. The finished system must work fully offline.
- Use PowerShell commands (Windows). Run commands only inside this project folder.
- Never claim that something is installed, fixed or working unless you ran a command that proves it. Show the real output.
- Skills and generic workflows: do NOT use any generic skill workflow (spec, plan or test files, brainstorming and so on). The stage definition in `PROJECT_CONTEXT.md` is the spec. If a skill conflicts with `PROJECT_CONTEXT.md` or this file, `PROJECT_CONTEXT.md` and this file win.
- At the end of every session update `progress/current_status.md` and STOP. Do not start the next stage.

## 3. Safety rules for files and commands
- NEVER run a delete command (`Remove-Item`, `rm`, `del`, `rmdir`, or anything equivalent) without first asking me. When you ask, show the FULL absolute path and list what is inside it.
- NEVER delete or overwrite the project root folder or any parent folder.
- NEVER delete or overwrite: `PROJECT_CONTEXT.md`, `AGENTS.md`, `.clinerules`, `progress/`, `known_faces/`, `embeddings/`, `data/`, `tests/data/`, `.git/`.
- `venv/` may be deleted and recreated only if I explicitly ask.
- Before creating a file, check whether it already exists. If it exists, read it first and edit it instead of overwriting it.
- If you are not sure whether something should be changed or deleted, do not touch it. List it under "NEEDS MY DECISION".
- Do not run `git commit`, `git reset`, `git checkout` or `git clean` unless I ask.

## 4. Final report format (English, at the end of every session)
- DONE: what you completed in this session.
- CHANGED / DELETED: every file you edited, moved, renamed or deleted, with its path and the reason.
- TESTS: the exact command you ran and the result, including skipped tests and why.
- REMAINING: the stages and open issues that are still left.
- NEEDS MY DECISION: anything you were unsure about or skipped.
