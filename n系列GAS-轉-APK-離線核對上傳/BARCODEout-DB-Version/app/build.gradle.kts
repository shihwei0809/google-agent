import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
}

// 讀取並自動遞增版本號
val versionPropsFile = file("version.properties")
val versionProps = Properties()

if (!versionPropsFile.exists()) {
    versionPropsFile.createNewFile()
    versionProps["VERSION_CODE"] = "1"
    versionProps["VERSION_NAME"] = "1.1"
    FileOutputStream(versionPropsFile).use { versionProps.store(it, null) }
}

FileInputStream(versionPropsFile).use { versionProps.load(it) }

var nextVersionCode = (versionProps["VERSION_CODE"] as String).toInt()
var nextVersionName = versionProps["VERSION_NAME"] as String

val runTasks = gradle.startParameter.taskNames
var isAssemble = false
for (task in runTasks) {
    val taskLower = task.lowercase()
    if (taskLower.contains("assemble") || taskLower.contains("bundle") || taskLower.contains("generate")) {
        isAssemble = true
        break
    }
}

if (isAssemble) {
    nextVersionCode += 1
    val parts = nextVersionName.split(".")
    nextVersionName = if (parts.size >= 2) {
        val major = parts[0]
        val minor = parts[1].toInt() + 1
        "$major.$minor"
    } else {
        "1.2"
    }
    
    versionProps["VERSION_CODE"] = nextVersionCode.toString()
    versionProps["VERSION_NAME"] = nextVersionName
    FileOutputStream(versionPropsFile).use { versionProps.store(it, "Auto-incremented during build") }
}

android {
    namespace = "com.example.barcode_out"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "com.example.barcode_out"
        minSdk = 26
        targetSdk = 36
        versionCode = nextVersionCode
        versionName = nextVersionName

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

// 封裝完自動改名為「N-系列出貨核對-v版本號.apk」
tasks.register("renameApk") {
    doLast {
        val versionName = android.defaultConfig.versionName ?: "x"
        val outDir = layout.buildDirectory.dir("outputs/apk/debug").get().asFile
        val oldFile = File(outDir, "app-debug.apk")
        val newFile = File(outDir, "N-系列出貨核對-v${versionName}.apk")
        if (newFile.exists()) newFile.delete()
        if (oldFile.exists()) {
            oldFile.renameTo(newFile)
            println("✅ APK 已命名為: ${newFile.name}")
        }
    }
}

afterEvaluate {
    tasks.named("assembleDebug") {
        finalizedBy("renameApk")
    }
}


dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.constraintlayout)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
// 替換成這個 ZXing 掃描套件
    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
    // 用於與 GAS 通訊及發送 Line
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}