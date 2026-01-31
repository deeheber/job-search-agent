# Job Search Agent

AI agent that finds hiring opportunities at companies using Tavily web search.

**Input**: Company name (+ optional title/location filters)
**Output**: Hiring status, matching positions, job links

## Quick Reference

```bash
# Agent: cd agent && source .venv/bin/activate
python src/agentcore_app.py     # Run locally
./quality-check.sh              # All checks (auto-fix)

# CDK: cd cdk
npm run cdk:deploy              # Deploy
npm run fix                     # Auto-fix linting
```

## Key Files

- `agent/src/agentcore_app.py` - Agent implementation
- `agent/src/secret_utils.py` - SSM secrets integration
- `cdk/lib/job-search-agent-stack.ts` - Infrastructure

## Detailed Standards

See `.kiro/steering/` for comprehensive guidance (shared with Kiro):
- `product.md` - Purpose and roadmap
- `tech.md` - Stack, commands, configuration
- `structure.md` - File organization
- `python-agent.md` - Python patterns (applies to `agent/**`)
- `typescript-cdk.md` - CDK patterns (applies to `cdk/**`)
