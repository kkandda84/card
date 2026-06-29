@echo off
chcp 65001 > nul
title 아모레몰 자동화 - 동작 녹화

echo.
echo =============================================
echo   아모레몰 동작 녹화 (Codegen)
echo =============================================
echo.
echo 브라우저가 열리면 직접 로그인 후 장바구니 담고 결제까지 진행하세요.
echo 모든 동작이 자동으로 recorded.py 파일에 저장됩니다.
echo.
echo 완료 후 브라우저를 닫으면 됩니다.
echo.
pause

call .venv\Scripts\activate.bat
playwright codegen --output recorded.py --lang python https://www.amoremall.com

echo.
echo 녹화 완료! recorded.py 파일을 확인하세요.
echo.
pause
