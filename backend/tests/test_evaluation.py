"""
Tests for Evaluation dataset integrity, chunking formulas, and evaluation metrics calculations.
"""

import json
import os
import sys

# Ensure repository root is on sys.path so 'evaluation' package is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from evaluation.evaluate import (
    calculate_token_overlap_similarity,
    chunk_document_text,
    judge_answer_correctness,
    judge_faithfulness,
    RAGConfig,
    run_evaluation_suite
)


def test_golden_dataset_structure():
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evaluation", "golden_dataset.json"))
    assert os.path.exists(dataset_path), f"Golden dataset missing at {dataset_path}"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_questions"] == 30
    assert len(data["questions"]) == 30

    required_fields = ["id", "document", "question", "ground_truth_context", "ground_truth_answer"]
    for q in data["questions"]:
        for field in required_fields:
            assert field in q, f"Field '{field}' missing from question {q.get('id')}"
            assert len(str(q[field]).strip()) > 0, f"Field '{field}' is empty in question {q.get('id')}"


def test_chunk_document_text_overlap():
    sample_text = "A" * 1000
    chunks = chunk_document_text(sample_text, chunk_size=400, chunk_overlap=100)
    assert len(chunks) > 1
    # Check that chunks do not exceed specified chunk_size
    assert all(len(c) <= 400 for c in chunks)


def test_token_overlap_similarity():
    text1 = "FastAPI powers high-performance Python REST APIs."
    text2 = "FastAPI is used to build high-performance Python APIs."
    sim = calculate_token_overlap_similarity(text1, text2)
    assert 0.5 <= sim <= 1.0

    # Completely disjoint text
    text3 = "Unrelated cooking recipe for apple pie."
    disjoint_sim = calculate_token_overlap_similarity(text1, text3)
    assert disjoint_sim == 0.0


def test_judge_answer_correctness_and_faithfulness():
    gt = "Employees accrue 18 days of paid time off per calendar year."
    pred = "According to company handbook, employees receive 18 days of paid time off each year."
    correctness = judge_answer_correctness(pred, gt)
    assert correctness >= 0.8

    contexts = ["Employees accrue 18 days of paid time off per calendar year."]
    faithfulness = judge_faithfulness(pred, contexts)
    assert faithfulness >= 0.60


def test_small_eval_suite_run():
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evaluation", "golden_dataset.json"))
    cfg = RAGConfig(
        name="Test Mini Config",
        chunk_size=500,
        chunk_overlap=100,
        top_k=3,
        enable_reranking=True
    )
    metrics, details = run_evaluation_suite(dataset_path, cfg)
    assert metrics.total_samples == 30
    assert 0.0 <= metrics.recall_at_k <= 1.0
    assert 0.0 <= metrics.mrr <= 1.0
    assert len(details) == 30
