# Agent Skills (OpenCode)

This project uses skills installed under .opencode/skills/ and compatible paths.

## Core Rules
- If a task matches a skill, invoke it with the skill tool before acting.
- Follow the skill workflow strictly; do not partially apply it.
- Never skip required steps such as spec, plan, or test when a skill demands them.

## Intent to Skill Mapping
- Feature / new functionality: spec-driven-development, then incremental-implementation and test-driven-development
- Planning / breakdown: planning-and-task-breakdown
- Bug / failure: debugging-and-error-recovery
- Code review: code-review-and-quality
- Refactoring: code-simplification
- API design: api-and-interface-design
- Security: security-and-hardening
- Performance: performance-optimization
