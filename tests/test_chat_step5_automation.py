"""Regresiones del ejecutor: evidencia, presupuestos y revisiones sin aprobar."""
from copy import deepcopy
import json
import socket

import pytest

from tests.chat_step5_automation import (PLAN_PATH, FixtureDB, CaseFailure, digest,
    select_cases, block_external_network, execute_case, validate_human_review, write_outputs, main)


@pytest.fixture
def plan():
    return json.loads(PLAN_PATH.read_text(encoding='utf-8'))


def test_first_selection_preserves_nine_posts_and_eighteen_attempts(plan):
    chosen = select_cases(plan, 'first')
    assert len(chosen) == 8
    assert sum(c['budget']['live_chat_posts_max'] for c in chosen) == 9
    assert sum(c['budget']['gemini_attempts_max'] for c in chosen) == 18


@pytest.mark.parametrize('selection', ['unknown', 'D01,D01', 'D01,', ''])
def test_bad_selection_rejected(plan, selection):
    with pytest.raises(AssertionError, match='invalid_case_selection'):
        select_cases(plan, selection)


def test_variants_never_modify_original_manifest(plan):
    original = deepcopy(plan)
    for variant in plan['fixtures']['variants']:
        fixture = FixtureDB(plan, variant)
        assert fixture.rows
    assert plan == original


def test_external_socket_blocked_without_contact():
    with block_external_network():
        with socket.socket() as client:
            with pytest.raises(RuntimeError, match='external_network_blocked'):
                client.connect(('192.0.2.1', 443))


def test_live_budget_rejected_before_loading_private_env(tmp_path):
    output = tmp_path / 'not_created'
    with pytest.raises(AssertionError, match='explicit_bounded_model_budget_required'):
        main(['--mode', 'gemini', '--cases', 'D01', '--max-model-calls', '3',
              '--private-env', str(tmp_path / 'missing'), '--output', str(output)])
    assert not output.exists()


def test_fixture_missing_metric_preserves_negative_and_read_only(plan):
    case = next(c for c in plan['cases'] if c['id'] == 'D08')
    with block_external_network():
        result = execute_case(case, plan)
    assert result['automation_status'] == 'passed'
    assert result['provider_calls'] == 0
    assert result['observations'][0]['body']['answer']['parts'][0]['status'] == 'not_found'


def test_failed_case_keeps_response_and_sanitizes_error(plan, monkeypatch):
    from tests import chat_step5_automation as module
    def fail(_case, harness, _plan):
        harness.answer()
        raise RuntimeError('pretend-secret-that-must-not-be-saved')
    monkeypatch.setattr(module, 'data_or_language', fail)
    with block_external_network(), pytest.raises(CaseFailure) as error:
        execute_case(plan['cases'][0], plan)
    assert error.value.failure_code == 'RuntimeError'
    assert error.value.observations[0]['status'] == 200
    assert 'pretend-secret' not in str(error.value)


def real_report():
    answer = {'parts': [{'message': 'Respuesta sintética para comprobar el importador.', 'generation_status': 'validated'}]}
    report = {'mode': 'gemini', 'cases': [{'id': 'L01', 'observations': [{'method': 'POST', 'body': {'answer': answer}}]}]}
    raw = json.dumps(report).encode()
    review = {'report_sha256': digest(raw), 'samples': [{'sample_id': 'L01-1',
        'response_sha256': digest(answer), 'answer': answer,
        'readers': {r: {'scores': [2, 2, 2, 1], 'understood_essential_meaning': True} for r in ('R1', 'R2')}}]}
    return raw, review


def test_human_review_requires_all_bound_responses_and_two_readers():
    raw, review = real_report()
    assert validate_human_review(review, raw)['status'] == 'passed'
    review['samples'][0]['readers'].pop('R2')
    with pytest.raises(AssertionError, match='two_readers_required'):
        validate_human_review(review, raw)


@pytest.mark.parametrize('change,code', [('blank', 'review_incomplete_scores'), ('tamper', 'review_response_mismatch'), ('omit', 'review_samples_incomplete'), ('low', 'clarity_not_approved')])
def test_review_does_not_pass_missing_adverse_or_changed_evidence(change, code):
    raw, review = real_report()
    if change == 'blank':
        review['samples'][0]['readers']['R1']['scores'] = [None] * 4
    elif change == 'tamper':
        review['samples'][0]['answer']['parts'][0]['message'] = 'Otro texto'
    elif change == 'omit':
        review['samples'] = []
    else:
        review['samples'][0]['readers']['R1']['scores'] = [2, 2, 2, 0]
    with pytest.raises(AssertionError, match=code):
        validate_human_review(review, raw)


def test_simulated_output_never_populates_real_clarity_samples(tmp_path):
    report = {'run_id': 'synthetic-run', 'mode': 'simulated', 'summary': {'passed': 1, 'failed': 0, 'not_run': 0},
              'provider_calls': 0, 'cases': [{'id': 'L01', 'automation_status': 'passed', 'pending_layers': ['real_provider']} ]}
    write_outputs(tmp_path, report)
    review = json.loads((tmp_path / 'human_review.json').read_text(encoding='utf-8'))
    assert review['samples'] == [] and review['status'] == 'pending'


def test_review_html_escapes_model_text_and_omits_fallback_samples(tmp_path):
    answer = {'parts': [{'message': '</script><img src=x onerror=alert(1)>', 'generation_status': 'validated'}]}
    report = {'run_id': 'synthetic', 'mode': 'gemini', 'summary': {'passed': 1, 'failed': 0, 'not_run': 0},
        'provider_calls': 0, 'cases': [{'id': 'L01', 'automation_status': 'passed', 'pending_layers': [], 'observations': [
            {'method': 'POST', 'body': {'answer': answer}},
            {'method': 'POST', 'body': {'answer': {'parts': [{'message': 'respaldo', 'generation_status': 'fallback'}]}}}]}]}
    write_outputs(tmp_path, report)
    review = json.loads((tmp_path / 'human_review.json').read_text(encoding='utf-8'))
    assert len(review['samples']) == 1
    html = (tmp_path / 'human_review.html').read_text(encoding='utf-8')
    assert '</script><img' not in html
    assert '\\u003c/script>' in html
