// 這是 Top-level 檔案，我們把所有插件的載入權限交給它，避免重複
plugins {
    id("com.android.application") version "9.1.1" apply false
    id("org.jetbrains.kotlin.android") version "2.2.10" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.10" apply false
}