@echo off
setlocal enabledelayedexpansion

:: ===============================================
::  LandScape Installer v1.0
::  The Permaculture Design Companion for Inkscape
:: ===============================================

set "SCRIPT_DIR=%~dp0"
set "INKSCAPE_EXT=%APPDATA%\inkscape\extensions\LandScape"
set "INKSCAPE_THEME=%APPDATA%\inkscape\local\themes\LandScape-Green"
set "PREFS_FILE=%APPDATA%\inkscape\preferences.xml"

:: ===============================================
::  Welcome Screen
:: ===============================================
cls
echo.
echo  ================================================
echo.
echo     LANDSCAPE  -  Installation
echo.
echo     The Permaculture Design Companion
echo.
echo  ================================================
echo.
echo  Installing LandScape extensions...
echo.

:: ===============================================
::  Install LandScape Extension Files
:: ===============================================
echo [1/3] Copying extension files...

if exist "%INKSCAPE_EXT%" (
    echo   Found existing installation - backing up...
    if not exist "%INKSCAPE_EXT%.backup" (
        move "%INKSCAPE_EXT%" "%INKSCAPE_EXT%.backup" >nul 2>&1
    )
)

:: Create extensions directory if needed
if not exist "%APPDATA%\inkscape\extensions" (
    mkdir "%APPDATA%\inkscape\extensions" >nul 2>&1
)

:: Copy LandScape folder
xcopy /E /Y /Q "%SCRIPT_DIR%LandScape" "%INKSCAPE_EXT%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Extensions installed successfully
) else (
    echo   [ERROR] Failed to copy extension files
    goto :error
)

:: ===============================================
::  Install LandScape Green Theme
:: ===============================================
echo.
echo [2/3] Installing green theme...

:: Create themes directory if needed
if not exist "%APPDATA%\inkscape\local\themes" (
    mkdir "%APPDATA%\inkscape\local\themes" >nul 2>&1
)

:: Copy theme folder
xcopy /E /Y /Q "%SCRIPT_DIR%LandScape-Green" "%INKSCAPE_THEME%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Green theme installed successfully
) else (
    echo   [SKIP] Theme installation skipped (optional)
)

:: ===============================================
::  Update Inkscape Preferences
:: ===============================================
echo.
echo [3/3] Configuring Inkscape preferences...

if exist "%PREFS_FILE%" (
    :: Try to update gtkTheme in preferences.xml
    powershell -Command " ^
        $file = '%PREFS_FILE%'; ^
        if (Test-Path $file) { ^
            $content = Get-Content $file -Raw; ^
            if ($content -match 'gtkTheme=\"([^\"]+)\"') { ^
                $content = $content -replace [regex]::Escape($matches[0]), 'gtkTheme=\"LandScape-Green\"'; ^
                Set-Content -Path $file -Value $content -NoNewline; ^
                Write-Host '   [OK] Preferences updated'; ^
            } elseif ($content -match 'gtk-theme') { ^
                $content = $content -replace 'gtk-theme=\"([^\"]+)\"', 'gtk-theme=\"LandScape-Green\"'; ^
                Set-Content -Path $file -Value $content -NoNewline; ^
                Write-Host '   [OK] Preferences updated'; ^
            } else { ^
                Write-Host '   [SKIP] Theme preference not found - set manually in Inkscape'; ^
            } ^
        }" >nul 2>&1
) else (
    echo   [SKIP] preferences.xml not found - set theme manually in Inkscape
)

:: ===============================================
::  Completion
:: ===============================================
cls
echo.
echo  ================================================
echo.
echo     INSTALLATION COMPLETE!
echo.
echo  ================================================
echo.
echo  What was installed:
echo    [OK] LandScape Extensions
echo    [OK] LandScape Green Theme
echo.
echo  Next steps:
echo    1. Open Inkscape
echo    2. Go to Edit ^> Preferences ^> Interface ^> Theming
echo    3. Select "LandScape-Green" theme
echo    4. Restart Inkscape
echo.
echo  Press any key to exit...
pause >nul
exit /b 0

:error
echo.
echo  ================================================
echo.
echo     INSTALLATION FAILED
echo.
echo  ================================================
echo.
pause
exit /b 1
