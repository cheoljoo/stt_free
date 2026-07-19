"""STT: 음성 파일 -> 타임스탬프 포함 전문(transcript). DESIGN.md 3-3 참고."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    language: str
    duration: float
    segments: list[Segment]

    @property
    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


def format_timestamp(seconds: float) -> str:
    td = dt.timedelta(seconds=max(0.0, seconds))
    total = int(td.total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def transcribe(audio_path: Path, cfg: dict) -> TranscriptResult:
    """faster-whisper로 오디오를 인식한다. cfg는 config.yaml의 stt 섹션."""
    from faster_whisper import WhisperModel

    model_size = cfg.get("model_size", "small")
    device = cfg.get("device", "cpu")
    compute_type = cfg.get("compute_type", "int8")
    language = cfg.get("language") or None

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments_iter, info = model.transcribe(str(audio_path), language=language)

    segments = [
        Segment(start=seg.start, end=seg.end, text=seg.text)
        for seg in segments_iter
    ]
    return TranscriptResult(
        language=info.language,
        duration=info.duration,
        segments=segments,
    )


def render_transcript_markdown(
    title: str, recorded_at: dt.datetime, result: TranscriptResult
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 녹음 시각: {recorded_at.strftime('%Y-%m-%d %H:%M')}",
        f"- 길이: {format_timestamp(result.duration)} / 언어: {result.language}",
        "",
        "---",
        "",
    ]
    for seg in result.segments:
        lines.append(f"[{format_timestamp(seg.start)}] {seg.text.strip()}")
    lines.append("")
    return "\n".join(lines)
