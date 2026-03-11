@echo off
chcp 65001 >nul
title GitSync - Синхронизация

echo ========================================
echo    GitSync - Автоматическая синхронизация
echo ========================================
echo.

REM Проверка наличия git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo ОШИБКА: Git не установлен!
    echo Скачайте с: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Настройка автоматического запуска...
echo.

REM Создаем задачу в планировщике для запуска при старте
schtasks /create /tn "GitSync" /tr "\"%CD%\sync.bat\"" /sc onlogon /f >nul 2>&1

echo ГОТОВ!
echo.
echo Синхронизация будет выполняться каждые 5 минут.
echo Закроете это окно - синхронизация продолжится в фоне.
echo.

:sync
echo [%date% %time:~0,8%] Синхронизация...
call git pull
if %errorlevel% equ 0 (
    echo [%date% %time:~0,8%] Успешно
) else (
    echo [%date% %time:~0,8%] Ошибка синхронизации
)
echo.

REM Ждем 5 минут (300 секунд)
timeout /t 300 /nobreak >nul
goto sync
