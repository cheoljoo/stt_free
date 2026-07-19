"""AI 분석: 전문(transcript) -> 요약/핵심/할일 + 원페이저용 구조 데이터. DESIGN.md 3-4 참고."""

from __future__ import annotations

import json
import subprocess

PROMPT_TEMPLATE = """\
다음은 한국어 음성/통화 녹음의 전사(transcript)입니다. 이 내용을 분석해서
아래 JSON 스키마에 맞는 결과만 출력하세요. 다른 설명이나 마크다운 코드펜스 없이
순수 JSON 객체 하나만 출력해야 합니다.

스키마:
{{
  "title": "짧은 제목 (10자 내외)",
  "three_line_summary": ["줄1", "줄2", "줄3"],
  "key_points": ["핵심 내용 bullet", ...],
  "decisions": ["결정/합의 사항", ...],
  "action_items": [{{"task": "할 일", "owner": "담당자 또는 미상", "due": "기한 또는 미상"}}, ...],
  "timeline": [{{"time": "MM:SS", "topic": "그 시점의 주제"}}, ...]
}}

내용이 없는 항목은 빈 배열로 두세요. timeline은 대화 흐름을 3~6개 구간으로 요약하세요.

--- 전사 시작 ---
{transcript}
--- 전사 끝 ---
"""

EMPTY_RESULT = {
    "title": "",
    "three_line_summary": [],
    "key_points": [],
    "decisions": [],
    "action_items": [],
    "timeline": [],
}


def _extract_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM 응답에서 JSON을 찾지 못했습니다: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def _call_claude_code(prompt: str, model: str) -> str:
    """`claude -p` 헤드리스 모드로 호출 (Claude Code 구독 내, 추가 API 비용 없음)."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    return result.stdout


def _call_claude_api(prompt: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _call_gemini(prompt: str, model: str) -> str:
    import google.generativeai as genai

    gm = genai.GenerativeModel(model or "gemini-1.5-flash")
    resp = gm.generate_content(prompt)
    return resp.text


def _call_ollama(prompt: str, model: str) -> str:
    import ollama

    resp = ollama.generate(model=model, prompt=prompt)
    return resp["response"]


def analyze(transcript_text: str, cfg: dict) -> dict:
    """cfg는 config.yaml의 analyze 섹션. backend: claude | claude-code | gemini | ollama | none."""
    backend = cfg.get("backend", "none")
    if backend == "none" or not transcript_text.strip():
        return dict(EMPTY_RESULT)

    prompt = PROMPT_TEMPLATE.format(transcript=transcript_text)

    if backend == "claude-code":
        raw = _call_claude_code(prompt, cfg.get("model", "claude-sonnet-5"))
    elif backend == "claude":
        raw = _call_claude_api(prompt, cfg.get("model", "claude-sonnet-5"))
    elif backend == "gemini":
        raw = _call_gemini(prompt, cfg.get("model", "gemini-1.5-flash"))
    elif backend == "ollama":
        raw = _call_ollama(prompt, cfg.get("ollama_model", "llama3.1"))
    else:
        raise ValueError(f"알 수 없는 analyze.backend: {backend}")

    data = _extract_json(raw)
    for key, default in EMPTY_RESULT.items():
        data.setdefault(key, default)
    return data
