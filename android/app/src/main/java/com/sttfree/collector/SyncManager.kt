package com.sttfree.collector

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

sealed class SyncResult {
    data class Success(val pushedCount: Int) : SyncResult()
    data class NotConfigured(val message: String) : SyncResult()
    data class Failure(val error: Throwable) : SyncResult()
}

/** 스캔 → 파일명 규칙 적용 → git push 를 한 번에 수행. */
class SyncManager(private val context: Context) {

    private val settings = SettingsStore(context)
    private val scanner = RecordingScanner(context)

    fun runSync(): SyncResult {
        if (!settings.isConfigured()) {
            return SyncResult.NotConfigured(context.getString(R.string.status_not_configured))
        }

        return try {
            val since = settings.lastScannedEpochSec
            val newRecordings = scanner.findNewRecordings(since)
            if (newRecordings.isEmpty()) {
                return SyncResult.Success(0)
            }

            val filesToWrite = newRecordings.associate { recording ->
                val inboxName = FileNaming.buildInboxFileName(recording)
                val bytes = context.contentResolver.openInputStream(recording.mediaStoreUri)
                    ?.use { it.readBytes() }
                    ?: ByteArray(0)
                File(inboxName) to bytes
            }.filterValues { it.isNotEmpty() }

            val pushed = GitRepoSync(context, settings).syncNewFiles(filesToWrite)

            val maxDate = newRecordings.maxOf { it.dateModifiedEpochSec }
            settings.lastScannedEpochSec = maxDate
            settings.lastSyncSummary = context.getString(
                R.string.status_success,
                SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date()),
                pushed,
            )
            SyncResult.Success(pushed)
        } catch (t: Throwable) {
            settings.lastSyncSummary = context.getString(R.string.status_error, t.message ?: t.toString())
            SyncResult.Failure(t)
        }
    }
}
