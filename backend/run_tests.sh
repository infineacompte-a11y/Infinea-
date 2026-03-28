#!/bin/bash
# InFinea — Run unit tests for critical AI services
# Usage: cd backend && bash run_tests.sh

set -e

echo "🧪 Running InFinea AI service unit tests..."
echo ""

python3 -m pytest tests/unit/test_scoring_engine.py \
                   tests/unit/test_coaching_engine.py \
                   tests/unit/test_knowledge_engine.py \
                   tests/unit/test_user_model.py \
                   tests/unit/test_ai_memory.py \
                   tests/unit/test_curriculum_adaptive.py \
                   -v --tb=short "$@"
