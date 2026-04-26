@echo off
cd /d "C:\Users\anesu\OneDrive\Desktop\3rd year Extra\IEEE IAS Competition\Tra-fix_server-main"
echo 🚀 Starting Traffic Server...
echo.
start "Python Server" cmd /k ".venv\Scripts\activate && python run.py"
timeout /t 3
echo 🔗 Starting ngrok tunnel...
start "Ngrok" cmd /k "ngrok http 9998 --request-header-add ngrok-skip-browser-warning:true"
timeout /t 3
cls
echo ========================================
echo ✅ SERVER IS RUNNING!
echo ========================================
echo.
echo 📍 LOCAL ACCESS (Your computer):
echo    http://127.0.0.1:9998
echo.
echo 📍 LOCAL NETWORK (Same WiFi):
echo    http://192.168.1.89:9998
echo.
echo 🌍 PUBLIC ACCESS (Mobile app team):
echo    Check the NGROK window for the URL
echo    It looks like: https://xxxx.ngrok-free.dev
echo.
echo ⚠️  IMPORTANT:
echo    - Keep BOTH terminal windows open
echo    - If ngrok says "reconnecting", close and restart
echo    - Share the ngrok URL with your team
echo.
echo ========================================
pause