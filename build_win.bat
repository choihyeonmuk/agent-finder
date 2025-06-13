@echo off

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 필요한 패키지 설치
pip install pyinstaller

REM 빌드 디렉토리 생성
if not exist dist mkdir dist

REM PyInstaller로 실행 파일 생성
pyinstaller --onefile ^
    --name agent-finder ^
    --add-data "venv\Lib\site-packages\customtkinter;customtkinter" ^
    --add-data "venv\Lib\site-packages\pillow;PIL" ^
    --windowed ^
    api_gui.py

REM 빌드 완료 메시지
echo 빌드가 완료되었습니다. 실행 파일은 dist\agent-finder.exe에 있습니다.