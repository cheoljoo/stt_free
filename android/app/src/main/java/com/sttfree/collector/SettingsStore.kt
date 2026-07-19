package com.sttfree.collector

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * 저장소 URL / GitHub 사용자명 / PAT을 Android Keystore로 암호화해 저장.
 * PAT+HTTPS만 지원 (SSH는 JGit 세션 팩토리 설정이 복잡해 1차 구현에서 제외 — DESIGN.md 3-1 참고).
 */
class SettingsStore(context: Context) {

    private val prefs = run {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "stt_free_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    var repoUrl: String?
        get() = prefs.getString(KEY_REPO_URL, null)
        set(value) = prefs.edit().putString(KEY_REPO_URL, value).apply()

    var username: String?
        get() = prefs.getString(KEY_USERNAME, null)
        set(value) = prefs.edit().putString(KEY_USERNAME, value).apply()

    var token: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(value) = prefs.edit().putString(KEY_TOKEN, value).apply()

    var lastSyncSummary: String?
        get() = prefs.getString(KEY_LAST_SYNC, null)
        set(value) = prefs.edit().putString(KEY_LAST_SYNC, value).apply()

    /** 마지막으로 스캔한 지점(epoch 초). 이 시각 이후 수정된 녹음만 새 파일로 취급. */
    var lastScannedEpochSec: Long
        get() = prefs.getLong(KEY_LAST_SCANNED, 0L)
        set(value) = prefs.edit().putLong(KEY_LAST_SCANNED, value).apply()

    fun isConfigured(): Boolean =
        !repoUrl.isNullOrBlank() && !username.isNullOrBlank() && !token.isNullOrBlank()

    companion object {
        private const val KEY_REPO_URL = "repo_url"
        private const val KEY_USERNAME = "username"
        private const val KEY_TOKEN = "token"
        private const val KEY_LAST_SYNC = "last_sync_summary"
        private const val KEY_LAST_SCANNED = "last_scanned_epoch_sec"
    }
}
