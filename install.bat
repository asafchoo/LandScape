@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===============================================
::  LandScape Installer v1.0
::  The Permaculture Design Companion for Inkscape
:: ===============================================

set "SCRIPT_DIR=%~dp0"
set "INKSCAPE_EXT=%APPDATA%\inkscape\extensions\LandScape"
set "INKSCAPE_THEME=%APPDATA%\inkscape\local\themes\LandScape-Green"
set "PREFS_FILE=%APPDATA%\inkscape\preferences.xml"

:: Colors
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "WHITE=[97m"
set "BOLD=[1m"
set "RESET=[0m"

:: ===============================================
::  Welcome Screen
:: ===============================================
cls
echo.
echo.  %CYAN%╔══════════════════════════════════════════════════╗%RESET%
echo.  %CYAN%║%RESET%  %BOLD%%WHITE%    LANDSCAPE  -  Installation    %RESET%           %CYAN%║%RESET%
echo.  %CYAN%║%RESET%  %GREEN%The Permaculture Design Companion%RESET%         %CYAN%║%RESET%
echo.  %CYAN%╚══════════════════════════════════════════════════╝%RESET%
echo.
echo.  %YELLOW%▶ Installing LandScape extensions...%RESET%
echo.

:: ===============================================
::  Install LandScape Extension Files
:: ===============================================
echo  %CYAN%[1/3]%RESET% Copying extension files...

if exist "%INKSCAPE_EXT%" (
    echo  %YELLOW%  Found existing installation - backing up...%RESET%
    if not exist "%INKSCAPE_EXT%.backup" (
        move "%INKSCAPE_EXT%" "%INKSCAPE_EXT%.backup" >nul
    )
)

:: Create extensions directory if needed
if not exist "%APPDATA%\inkscape\extensions" (
    mkdir "%APPDATA%\inkscape\extensions"
)

:: Copy LandScape folder
xcopy /E /Y /Q "%SCRIPT_DIR%LandScape" "%INKSCAPE_EXT%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo  %GREEN%  ✓%RESET% Extensions installed successfully
) else (
    echo  %RED%  ✗%RESET% Failed to copy extension files
    goto :error
)

:: ===============================================
::  Install LandScape Green Theme
:: ===============================================
echo.
echo  %CYAN%[2/3]%RESET% Installing green theme...

:: Create themes directory if needed
if not exist "%APPDATA%\inkscape\local\themes" (
    mkdir "%APPDATA%\inkscape\local\themes"
)

:: Copy theme folder
xcopy /E /Y /Q "%SCRIPT_DIR%LandScape-Green" "%INKSCAPE_THEME%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo  %GREEN%  ✓%RESET% Green theme installed successfully
) else (
    echo  %YELLOW%  !%RESET% Theme installation skipped (optional)
)

:: ===============================================
::  Update Inkscape Preferences
:: ===============================================
echo.
echo  %CYAN%[3/3]%RESET% Configuring Inkscape preferences...

if exist "%PREFS_FILE%" (
    :: Check current gtkTheme setting and replace
    powershell -Command "^
        $file = '%PREFS_FILE%';^
        $content = Get-Content $file -Raw;^
        if ($content -match 'gtkTheme=\"([^\"]+)\"') {^
            $content = $content -replace [regex]::Escape($matches[0]), 'gtkTheme=\"LandScape-Green\"';^
            Write-Host '  Found existing theme, updating...';^
        } else {^
            $content = $content -replace '(defaultGtkTheme=)', '$1 gtkTheme=\"LandScape-Green\" ';^
            Write-Host '  Adding theme preference...';^
        };^
        Set-Content -Path $file -Value $content -NoNewline;^
        Write-Host '  Done';^
        " >nul 2>&1
    
    if !errorlevel! equ 0 (
        echo  %GREEN%  ✓%RESET% Preferences updated
    ) else (
        echo  %YELLOW%  !%RESET% Could not update preferences (manual setting available)
    )
) else (
    echo  %YELLOW%  !%RESET% preferences.xml not found - set theme manually in Inkscape
)

:: ===============================================
::  Completion
:: ===============================================
cls
echo.
echo.  %GREEN%╔══════════════════════════════════════════════════╗%RESET%
echo.  %GREEN%║%RESET%  %BOLD%%WHITE%           INSTALLATION COMPLETE!           %RESET%           %GREEN%║%RESET%
echo.  %GREEN%╚══════════════════════════════════════════════════╝%RESET%
echo.
echo.  %WHITE%What was installed:%RESET%
echo.    %GREEN%✓%RESET% LandScape Extensions
echo.    %GREEN%✓%RESET% LandScape Green Theme
echo.
echo.  %YELLOW%Next steps:%RESET%
echo.    1. %WHITE%Open Inkscape%RESET%
echo.    2. %WHITE%Go to%RESET% ^ Edit ^ ^ Preferences ^ ^ Interface ^ ^ Theming
echo.    3. %WHITE%Select%RESET% "LandScape-Green" theme
echo.    4. %WHITE%Restart Inkscape%RESET%
echo.
echo.  %CYAN%To open Inkscape now? (Y/N):%RESET% 

set /p "choice="
if /i "!choice!"=="Y" (
    start "" "inkscape"
)
echo.
pause
exit /b 0

:error
echo.
echo.  %RED%╔═══════════════════════════════════════╗%RESET%
echo.  %RED%║%RESET%       %BOLD%INSTALLATION FAILED%RESET%              %RED%║%RESET%
echo.  %RED%╚═══════════════════════════════════════╝%RESET%
echo.
pause
exit /b 1
