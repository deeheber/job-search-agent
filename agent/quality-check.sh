#!/bin/bash

echo "Starting Python quality checks..."

if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in agent directory. Please run from agent/ folder."
    exit 1
fi

echo "Running tests..."
if uv run pytest; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi

echo "Running type checking..."
if uv run mypy src/; then
    echo "✅ Type checking passed"
else
    echo "❌ Type checking failed"
    exit 1
fi

echo "Running linting with autofix..."
if uv run ruff check --fix .; then
    echo "✅ Linting passed (issues auto-fixed)"
else
    echo "❌ Linting failed (some issues couldn't be auto-fixed)"
    exit 1
fi

echo "Formatting code..."
if uv run black .; then
    echo "✅ Code formatted successfully"
else
    echo "❌ Code formatting failed"
    exit 1
fi

echo "✅ All quality checks passed!"
