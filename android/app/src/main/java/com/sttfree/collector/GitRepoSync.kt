package com.sttfree.collector

import android.content.Context
import org.eclipse.jgit.api.Git
import org.eclipse.jgit.transport.UsernamePasswordCredentialsProvider
import java.io.File

/**
 * 앱 내부 저장소 clone을 유지하며 add/commit/push를 수행한다.
 * PAT+HTTPS 인증만 지원 (DESIGN.md 3-1 방법 B 참고).
 */
class GitRepoSync(context: Context, private val settings: SettingsStore) {

    private val repoDir = File(context.filesDir, "stt_free_repo")

    /** inbox/ 에 새 파일들을 커밋 & push. 반환값은 push된 파일 개수. */
    fun syncNewFiles(files: Map<File, ByteArray>): Int {
        val url = settings.repoUrl ?: error("저장소 URL이 설정되지 않았습니다.")
        val credentials = UsernamePasswordCredentialsProvider(settings.username, settings.token)

        val git = openOrClone(url, credentials)
        git.use {
            // 원격에 결과물(transcripts/summaries 등)이 새로 생겼을 수 있으므로 push 전 pull
            it.pull().setCredentialsProvider(credentials).call()

            val inboxDir = File(repoDir, "inbox").apply { mkdirs() }
            var written = 0
            for ((relativeFile, bytes) in files) {
                val target = File(inboxDir, relativeFile.name)
                target.writeBytes(bytes)
                written++
            }
            if (written == 0) return 0

            it.add().addFilepattern("inbox").call()
            val status = it.status().call()
            if (status.isClean) return 0

            it.commit()
                .setMessage("inbox: 새 음성 파일 추가 (Android 앱, ${written}건)")
                .call()
            it.push().setCredentialsProvider(credentials).call()
            return written
        }
    }

    private fun openOrClone(url: String, credentials: UsernamePasswordCredentialsProvider): Git {
        return if (repoDir.exists() && File(repoDir, ".git").exists()) {
            Git.open(repoDir)
        } else {
            repoDir.deleteRecursively()
            Git.cloneRepository()
                .setURI(url)
                .setDirectory(repoDir)
                .setCredentialsProvider(credentials)
                .call()
        }
    }
}
