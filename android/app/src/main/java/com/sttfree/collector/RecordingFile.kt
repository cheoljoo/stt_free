package com.sttfree.collector

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** 스캔으로 찾은 녹음 파일 한 건. */
data class RecordingFile(
    val mediaStoreUri: android.net.Uri,
    val displayName: String,
    val dateModifiedEpochSec: Long,
    val isCallRecording: Boolean,
)

/**
 * phone/auto_push.sh 와 동일한 파일명 규칙을 적용한다: DESIGN.md "파일명 규칙" 절 참고.
 * {YYYY-MM-DD}_{HHMM}_{call|memo}_{원본이름}.{ext}
 */
object FileNaming {
    private val timestampFormat = SimpleDateFormat("yyyy-MM-dd_HHmm", Locale.US)

    fun buildInboxFileName(source: RecordingFile): String {
        val ts = timestampFormat.format(Date(source.dateModifiedEpochSec * 1000))
        val kind = if (source.isCallRecording) "call" else "memo"
        val dotIndex = source.displayName.lastIndexOf('.')
        val base = if (dotIndex > 0) source.displayName.substring(0, dotIndex) else source.displayName
        val ext = if (dotIndex > 0) source.displayName.substring(dotIndex + 1) else "m4a"
        val sanitizedBase = base.replace(Regex("\\s+"), "_")
        return "${ts}_${kind}_${sanitizedBase}.${ext}"
    }
}
