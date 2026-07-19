pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // JGit 릴리스가 Maven Central에 없는 경우 Eclipse JGit 저장소 사용
        maven { url = uri("https://repo.eclipse.org/content/groups/releases/") }
    }
}

rootProject.name = "stt_free_collector"
include(":app")
