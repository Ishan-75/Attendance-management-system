@echo off
echo =========================================================
echo WorkforceHub Attendance System - Android APK Builder
echo =========================================================

cd /d "%~dp0\frontend"
echo [1/3] Building frontend production assets...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [2/3] Syncing assets with native Android project...
call npx cap sync android
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Capacitor sync failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Compiling Android APK...
cd android
call gradlew.bat assembleDebug
if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================================
    echo [SUCCESS] Android APK built successfully!
    echo Location: %~dp0frontend\android\app\build\outputs\apk\debug\app-debug.apk
    echo =========================================================
    explorer "%~dp0frontend\android\app\build\outputs\apk\debug"
) else (
    echo.
    echo [NOTE] Gradle build failed or JDK is not installed in PATH.
    echo You can open this project directly in Android Studio:
    echo 1. Open Android Studio
    echo 2. Open folder: %~dp0frontend\android
    echo 3. Click: Build ^> Build Bundle(s) / APK(s) ^> Build APK(s)
)

pause
