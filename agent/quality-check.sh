#!/bin/bash

# Python Quality Check Script
# Run from the agent directory

echo "🔍 Starting Python quality checks..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in agent directory. Please run from agent/ folder."
    exit 1
fi

# Check if we're already in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "📦 Already in virtual environment: $VIRTUAL_ENV"
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Warning: No virtual environment found at .venv"
fi

# Run quality checks
echo "🧪 Running tests..."
if pytest; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi

echo "🔍 Running type checking..."
if mypy src/; then
    echo "✅ Type checking passed"
else
    echo "❌ Type checking failed"
    exit 1
fi

echo "🔧 Running linting with autofix..."
if ruff check --fix .; then
    echo "✅ Linting passed (issues auto-fixed)"
else
    echo "❌ Linting failed (some issues couldn't be auto-fixed)"
    exit 1
fi

echo "🎨 Formatting code..."
if black .; then
    echo "✅ Code formatted successfully"
else
    echo "❌ Code formatting failed"
    exit 1
fi

echo "🎉 All quality checks passed!"