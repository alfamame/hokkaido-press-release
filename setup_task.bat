@echo off
REM ================================================================
REM 北海道金融機関プレスリリース 毎日8時自動実行 タスク登録スクリプト
REM 管理者権限で実行してください
REM ================================================================

SET TASK_NAME=HokkaidoPressRelease
SET SCRIPT_DIR=%~dp0
SET PYTHON_EXE=python

REM Pythonのフルパスを取得
FOR /F "tokens=*" %%i IN ('where python') DO (
    SET PYTHON_EXE=%%i
    GOTO :found_python
)
:found_python

REM 既存タスクを削除（エラー無視）
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

REM タスクを登録（毎日08:00に実行）
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_EXE%\" \"%SCRIPT_DIR%main.py\"" ^
    /sc daily ^
    /st 08:00 ^
    /rl highest ^
    /f

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ タスクスケジューラへの登録が完了しました。
    echo   タスク名: %TASK_NAME%
    echo   実行時刻: 毎日 08:00
    echo   スクリプト: %SCRIPT_DIR%main.py
    echo.
    echo タスクの確認: schtasks /query /tn "%TASK_NAME%"
    echo 今すぐテスト: schtasks /run /tn "%TASK_NAME%"
) ELSE (
    echo.
    echo ✗ タスク登録に失敗しました。管理者権限で実行してください。
)

pause
