@echo off
chcp 65001 > nul
title 아모레몰 결제 자동화

echo.
echo =============================================
echo   아모레몰 결제 자동화
echo =============================================
echo.

:: Python 설치 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되지 않았습니다.
    echo   https://www.python.org 에서 Python 3.x 를 설치하세요.
    pause
    exit /b 1
)

:: 의존성 설치 (최초 1회)
if not exist ".venv" (
    echo [설치] 가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

:: 패키지 설치 여부 확인
python -c "import playwright" > nul 2>&1
if %errorlevel% neq 0 (
    echo [설치] 패키지 설치 중...
    pip install -r requirements.txt -q
    echo [설치] Playwright 브라우저 설치 중...
    playwright install chromium
    echo.
)

:: .env 파일 없으면 안내
if not exist ".env" (
    echo [안내] .env 파일이 없습니다.
    echo   .env.example 을 복사해서 .env 를 만들고
    echo   아이디와 비밀번호를 입력해두면 자동으로 로그인됩니다.
    echo   없어도 실행 시 직접 입력할 수 있습니다.
    echo.
)

:: 상품번호 입력
set /p PRODUCT_INPUT="구매할 상품번호 입력 (여러 개는 쉼표로 구분): "

if "%PRODUCT_INPUT%"=="" (
    echo [오류] 상품번호를 입력해야 합니다.
    pause
    exit /b 1
)

echo.
echo [시작] 자동화를 시작합니다...
echo.

:: 쉼표로 구분된 상품번호를 공백으로 변환해서 인자로 전달
set ARGS=%PRODUCT_INPUT:,= %
python amoremall.py %ARGS%

echo.
if %errorlevel% equ 0 (
    echo =============================================
    echo   완료! 브라우저를 확인하세요.
    echo =============================================
) else (
    echo =============================================
    echo   오류가 발생했습니다. 위 메시지를 확인하세요.
    echo =============================================
)

echo.
pause
