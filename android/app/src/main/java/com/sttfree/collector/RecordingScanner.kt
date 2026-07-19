package com.sttfree.collector

import android.content.ContentUris
import android.content.Context
import android.provider.MediaStore

/**
 * MediaStore.Audio 쿼리로 녹음/통화녹음을 찾는다.
 * Termux 스크립트(auto_push.sh)처럼 기기별 절대경로(/sdcard/Recordings 등)를 하드코딩하는 대신,
 * RELATIVE_PATH에 "record"/"call" 문자열이 포함되는지로 분류한다 — 제조사별 폴더명이 달라도 더 안정적으로 동작.
 */
class RecordingScanner(private val context: Context) {

    fun findNewRecordings(sinceEpochSec: Long): List<RecordingFile> {
        val results = mutableListOf<RecordingFile>()
        val collection = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
        val projection = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.DISPLAY_NAME,
            MediaStore.Audio.Media.DATE_MODIFIED,
            MediaStore.Audio.Media.RELATIVE_PATH,
        )
        val selection = "${MediaStore.Audio.Media.DATE_MODIFIED} > ?"
        val selectionArgs = arrayOf(sinceEpochSec.toString())

        context.contentResolver.query(
            collection,
            projection,
            selection,
            selectionArgs,
            "${MediaStore.Audio.Media.DATE_MODIFIED} ASC",
        )?.use { cursor ->
            val idCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val nameCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DISPLAY_NAME)
            val dateCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DATE_MODIFIED)
            val pathCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.RELATIVE_PATH)

            while (cursor.moveToNext()) {
                val id = cursor.getLong(idCol)
                val name = cursor.getString(nameCol) ?: continue
                val dateModified = cursor.getLong(dateCol)
                val relativePath = cursor.getString(pathCol) ?: ""

                if (!isSupportedExtension(name)) continue

                val uri = ContentUris.withAppendedId(collection, id)
                val isCall = relativePath.contains("call", ignoreCase = true) ||
                    name.contains("call", ignoreCase = true)

                results.add(RecordingFile(uri, name, dateModified, isCall))
            }
        }
        return results
    }

    private fun isSupportedExtension(name: String): Boolean {
        val ext = name.substringAfterLast('.', "").lowercase()
        return ext in setOf("m4a", "mp3", "wav", "aac", "3gp", "amr")
    }
}
