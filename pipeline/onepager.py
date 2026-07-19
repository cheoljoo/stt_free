"""1페이지 시각화: 분석 JSON -> HTML 원페이저 (+선택적 PNG). DESIGN.md 3-5 참고."""

from __future__ import annotations

import datetime as dt
import html
from pathlib import Path

HTML_TEMPLATE = """\
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{
    font-family: -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    margin: 0; padding: 32px; background: #f5f6f8; color: #1a1a1a;
  }}
  .sheet {{
    max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px;
    padding: 32px 40px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  h1 {{ font-size: 24px; margin: 0 0 4px; }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
  .summary {{
    background: #eef4ff; border-left: 4px solid #3b6fd6; border-radius: 6px;
    padding: 14px 18px; margin-bottom: 24px; font-size: 15px; line-height: 1.6;
  }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  .card {{ background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 16px 20px; }}
  .card h2 {{ font-size: 15px; margin: 0 0 10px; color: #333; }}
  ul {{ margin: 0; padding-left: 18px; font-size: 14px; line-height: 1.7; }}
  .action-items li {{ list-style: none; margin-left: -18px; }}
  .action-items input {{ margin-right: 6px; }}
  .owner {{ color: #888; font-size: 12px; }}
  .timeline {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .tl-item {{
    background: #fff; border: 1px solid #ddd; border-radius: 999px;
    padding: 6px 12px; font-size: 12px; white-space: nowrap;
  }}
  .tl-time {{ font-weight: 600; color: #3b6fd6; margin-right: 6px; }}
  .empty {{ color: #aaa; font-size: 13px; }}
</style>
</head>
<body>
<div class="sheet">
  <h1>{title}</h1>
  <div class="meta">{recorded_at} · 길이 {duration}</div>

  <div class="summary">
    {three_line_summary}
  </div>

  <div class="grid">
    <div class="card">
      <h2>핵심 내용</h2>
      {key_points}
    </div>
    <div class="card">
      <h2>결정 사항</h2>
      {decisions}
    </div>
  </div>

  <div class="card" style="margin-bottom:24px;">
    <h2>할 일</h2>
    {action_items}
  </div>

  <div class="card">
    <h2>대화 흐름</h2>
    <div class="timeline">
      {timeline}
    </div>
  </div>
</div>
</body>
</html>
"""


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _bullet_list(items: list[str]) -> str:
    if not items:
        return '<div class="empty">내용 없음</div>'
    return "<ul>" + "".join(f"<li>{_esc(i)}</li>" for i in items) + "</ul>"


def _action_items(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">내용 없음</div>'
    rows = []
    for it in items:
        task = _esc(it.get("task", ""))
        owner = _esc(it.get("owner", "미상"))
        due = _esc(it.get("due", "미상"))
        rows.append(
            f'<li><input type="checkbox" disabled> {task} '
            f'<span class="owner">(담당: {owner}, 기한: {due})</span></li>'
        )
    return '<ul class="action-items">' + "".join(rows) + "</ul>"


def _timeline(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">내용 없음</div>'
    chips = []
    for it in items:
        time = _esc(it.get("time", ""))
        topic = _esc(it.get("topic", ""))
        chips.append(f'<div class="tl-item"><span class="tl-time">{time}</span>{topic}</div>')
    return "".join(chips)


def render_html(
    title: str,
    recorded_at: dt.datetime,
    duration_str: str,
    analysis: dict,
) -> str:
    summary_lines = analysis.get("three_line_summary") or []
    summary_html = (
        "<br>".join(_esc(line) for line in summary_lines)
        if summary_lines
        else '<span class="empty">요약 없음</span>'
    )
    return HTML_TEMPLATE.format(
        title=_esc(title),
        recorded_at=_esc(recorded_at.strftime("%Y-%m-%d %H:%M")),
        duration=_esc(duration_str),
        three_line_summary=summary_html,
        key_points=_bullet_list(analysis.get("key_points") or []),
        decisions=_bullet_list(analysis.get("decisions") or []),
        action_items=_action_items(analysis.get("action_items") or []),
        timeline=_timeline(analysis.get("timeline") or []),
    )


def render_png(html_path: Path, png_path: Path) -> bool:
    """playwright로 HTML을 PNG로 캡처. 미설치 시 False 반환하고 HTML만 남긴다."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1200})
        page.goto(html_path.resolve().as_uri())
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()
    return True
