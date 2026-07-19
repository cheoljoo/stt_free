package com.sttfree.collector

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        when (val result = SyncManager(applicationContext).runSync()) {
            is SyncResult.Success ->
                Result.success(workDataOf("pushedCount" to result.pushedCount))
            is SyncResult.NotConfigured ->
                Result.failure(workDataOf("error" to result.message))
            is SyncResult.Failure ->
                Result.retry()
        }
    }

    companion object {
        const val UNIQUE_WORK_NAME = "stt_free_periodic_sync"
    }
}
