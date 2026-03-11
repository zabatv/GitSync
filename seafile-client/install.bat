@echo off
chcp 65001 >nul
title Seafile Sync - Установка

echo ========================================
echo    Seafile Sync - Автоматическая установка
echo ========================================
echo.

REM === КОНФИГУРАЦИЯ ===
set SEAFILE_URL=https://seafile.yourserver.com
set LIBRARY_SYNC_LINK=ВАША_ССЫЛКА_СИНХРОНИЗАЦИИ
set SEAFILE_DATA=C:\SeafileData

REM Проверка админа
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Запустите от имени администратора!
    pause
    exit /b 1
)

echo [1/4] Проверка Seafile...
where seaf-cli.exe >nul 2>nul
if %errorlevel% equ 0 (
    echo Seafile уже установлен
    goto :sync
)

echo [2/4] Скачивание Seafile Client...
powershell -Command "Invoke-WebRequest -Uri 'https://download.seafile.com/d/436bb1bab1b2d2e473e5/files/3/Seafile-9.0.5.msi' -OutFile 'seafile.msi'" 2>nul

if not exist seafile.msi (
    echo Ошибка скачивания. Используйте ручную установку.
    echo Скачайте: https://www.seafile.com/download/
    pause
    exit /b 1
)

echo [3/4] Установка Seafile...
msiexec /i seafile.msi /quiet /norestart
del seafile.msi

REM Ждём установку
timeout /t 10 /nobreak >nul

:sync
echo [4/4] Настройка синхронизации...

REM Инициализация
seaf-cli initialize -d "%SEAFILE_DATA%"

REM Синхронизация
seaf-cli sync -l "%LIBRARY_SYNC_LINK%" -d "%SEAFILE_DATA%\Проект" -u "%SEAFILE_URL%"

echo.
echo ========================================
echo  УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Синхронизация работает в фоне.
echo Файлы появятся в: %SEAFILE_DATA%\Проект
echo.

REM Запуск при старте
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v SeafileSync /t REG_SZ /d "\"%ProgramFiles%\Seafile\Seafile Tray.exe\" -d %SEAFILE_DATA%" /f >nul 2>&1

pause
