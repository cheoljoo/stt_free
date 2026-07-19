"""엔트리포인트: inbox 스캔 -> STT -> 분석 -> 원페이저 -> archive 이동. DESIGN.md 4 참고."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
import traceback
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyze as analyze_mod
import onepager as onepager_mod
import stt as stt_mod

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac", ".3gp", ".amr"}
REPO_ROOT = Path(__file__).resolve().parent.parent


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_recorded_at(stem: str) -> dt.datetime:
    """파일명 규칙 {YYYY-MM-DD}_{HHMM}_... 에서 녹음 시각을 뽑는다. 실패 시 파일 mtime 사용."""
    parts = stem.split("_")
    if len(parts) >= 2:
        try:
            return dt.datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y-%m-%d_%H%M")
        except ValueError:
            pass
    return dt.datetime.now()


def output_paths(cfg: dict, stem: str) -> dict[str, Path]:
    p = cfg["paths"]
    return {
        "transcript": REPO_ROOT / p["transcripts"] / f"{stem}.md",
        "summary": REPO_ROOT / p["summaries"] / f"{stem}.md",
        "onepager_html": REPO_ROOT / p["onepagers"] / f"{stem}.html",
        "onepager_png": REPO_ROOT / p["onepagers"] / f"{stem}.png",
    }


def is_already_processed(cfg: dict, stem: str) -> bool:
    outs = output_paths(cfg, stem)
    return outs["transcript"].exists() and outs["summary"].exists() and outs["onepager_html"].exists()


def render_summary_markdown(title: str, recorded_at: dt.datetime, analysis: dict) -> str:
    lines = [f"# {title}", "", f"- 녹음 시각: {recorded_at.strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append("## 3줄 요약")
    for line in analysis.get("three_line_summary") or []:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## 핵심 내용")
    for item in analysis.get("key_points") or []:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 결정 사항")
    for item in analysis.get("decisions") or []:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 할 일")
    for item in analysis.get("action_items") or []:
        task = item.get("task", "")
        owner = item.get("owner", "미상")
        due = item.get("due", "미상")
        lines.append(f"- [ ] {task} (담당: {owner}, 기한: {due})")
    lines.append("")
    return "\n".join(lines)


def process_one(audio_path: Path, cfg: dict, skip_llm: bool = False) -> None:
    stem = audio_path.stem
    print(f"[run] 처리 시작: {audio_path.name}")

    if is_already_processed(cfg, stem):
        print(f"[run]   이미 처리됨, 건너뜀: {stem}")
        return

    recorded_at = parse_recorded_at(stem)
    outs = output_paths(cfg, stem)
    for out in outs.values():
        out.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1) STT
        print("[run]   1/3 STT 중...")
        result = stt_mod.transcribe(audio_path, cfg["stt"])
        transcript_md = stt_mod.render_transcript_markdown(stem, recorded_at, result)
        outs["transcript"].write_text(transcript_md, encoding="utf-8")

        # 2) 분석
        print("[run]   2/3 AI 분석 중...")
        analyze_cfg = dict(cfg["analyze"])
        if skip_llm:
            analyze_cfg["backend"] = "none"
        elif os.environ.get("STT_FREE_ANALYZE_BACKEND"):
            analyze_cfg["backend"] = os.environ["STT_FREE_ANALYZE_BACKEND"]
        analysis = analyze_mod.analyze(result.full_text, analyze_cfg)
        title = analysis.get("title") or stem
        outs["summary"].write_text(
            render_summary_markdown(title, recorded_at, analysis), encoding="utf-8"
        )

        # 3) 원페이저
        print("[run]   3/3 원페이저 생성 중...")
        duration_str = stt_mod.format_timestamp(result.duration)
        html_content = onepager_mod.render_html(title, recorded_at, duration_str, analysis)
        outs["onepager_html"].write_text(html_content, encoding="utf-8")

        if cfg.get("onepager", {}).get("render_png", True):
            ok = onepager_mod.render_png(outs["onepager_html"], outs["onepager_png"])
            if not ok:
                print("[run]   playwright 미설치, PNG 생성 건너뜀 (HTML만 생성됨)")

        # 4) archive 이동
        archive_dir = REPO_ROOT / cfg["paths"]["archive"] / f"{recorded_at.year:04d}" / f"{recorded_at.month:02d}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(audio_path), str(archive_dir / audio_path.name))

        error_log = audio_path.with_suffix(audio_path.suffix + ".error.log")
        if error_log.exists():
            error_log.unlink()

        print(f"[run] 완료: {stem}")

    except Exception:
        error_log = audio_path.with_suffix(audio_path.suffix + ".error.log")
        error_log.write_text(traceback.format_exc(), encoding="utf-8")
        print(f"[run] 실패: {stem} (자세한 내용: {error_log.name})", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="stt_free 파이프라인 실행")
    parser.add_argument("--config", default=str(REPO_ROOT / "pipeline" / "config.yaml"))
    parser.add_argument("--file", help="특정 파일 하나만 처리 (inbox 스캔 대신)")
    parser.add_argument("--skip-llm", action="store_true", help="AI 분석 단계를 건너뜀 (STT만 테스트)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    if args.file:
        process_one(Path(args.file).resolve(), cfg, skip_llm=args.skip_llm)
        return

    inbox = REPO_ROOT / cfg["paths"]["inbox"]
    audio_files = sorted(
        f for f in inbox.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    )
    if not audio_files:
        print("[run] inbox에 처리할 음성 파일이 없습니다.")
        return

    for audio_path in audio_files:
        process_one(audio_path, cfg, skip_llm=args.skip_llm)


if __name__ == "__main__":
    main()
