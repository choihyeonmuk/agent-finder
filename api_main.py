"""
API 기반 메인 실행 파일
부동산 중개사무소 정보 크롤링 프로그램의 API 기반 메인 실행 파일입니다.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication

# 프로젝트 모듈 임포트
from api_gui import ApiRealEstateGUI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApiRealEstateApp')

def main():
    """메인 함수"""
    try:
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        
        # GUI 생성 및 표시
        gui = ApiRealEstateGUI()
        gui.show()
        
        # 애플리케이션 실행
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
