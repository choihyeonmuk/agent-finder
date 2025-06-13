#!/bin/bash

# 가상환경 활성화
source venv/bin/activate

# 필요한 패키지 설치
pip install pyinstaller customtkinter pillow

# 빌드 디렉토리 생성
mkdir -p dist

# 실제 경로 확인
CUSTOMTKINTER_PATH=$(find venv -name "customtkinter" -type d | head -n 1)
PILLOW_PATH=$(find venv -name "PIL" -type d | head -n 1)

if [ -z "$CUSTOMTKINTER_PATH" ] || [ -z "$PILLOW_PATH" ]; then
    echo "필요한 패키지를 찾을 수 없습니다. 패키지 설치를 확인해주세요."
    exit 1
fi

# PyInstaller로 실행 파일 생성
pyinstaller --onefile \
    --name agent-finder \
    --add-data "$CUSTOMTKINTER_PATH:customtkinter" \
    --add-data "$PILLOW_PATH:PIL" \
    --windowed \
    api_gui.py

# 빌드 완료 메시지
echo "빌드가 완료되었습니다. 실행 파일은 dist/agent-finder.app에 있습니다."