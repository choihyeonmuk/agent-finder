"""
CSV 내보내기 모듈
크롤링한 부동산 중개사무소 정보를 CSV 파일로 내보내는 모듈입니다.
"""

import os
import pandas as pd
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataExporter')

class DataExporter:
    """부동산 중개사무소 정보 CSV 내보내기 클래스"""

    def __init__(self):
        """내보내기 모듈 초기화"""
        self.default_directory = os.path.expanduser("~/Documents/부동산_크롤링")

        # 기본 디렉토리 생성
        os.makedirs(self.default_directory, exist_ok=True)

    def clean_data(self, data):
        """
        데이터 정제 및 구조화

        Args:
            data (list): 크롤링한 원본 데이터 리스트

        Returns:
            pandas.DataFrame: 정제된 데이터 프레임
        """
        try:
            if not data:
                logger.warning("정제할 데이터가 없습니다.")
                return pd.DataFrame()

            # 데이터프레임 생성
            df = pd.DataFrame(data)

            # 중복 제거
            df = df.drop_duplicates()

            # 빈 값 처리
            df = df.fillna("")

            # 열 순서 정렬
            columns = [
                "시도", "시군구", "읍면동", "상호", "대표자명",
                "전화번호", "모바일전화번호", "주소"  # 모바일전화번호 컬럼 추가
            ]

            # 필요한 열만 선택 (존재하는 경우)
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]

            logger.info(f"데이터 정제 완료: {len(df)}개 항목")
            return df
        except Exception as e:
            logger.error(f"데이터 정제 실패: {str(e)}")
            return pd.DataFrame()

    def export_to_csv(self, data, filename=None, directory=None):
        """
        데이터를 CSV 파일로 내보내기

        Args:
            data (list): 크롤링한 원본 데이터 리스트
            filename (str, optional): 저장할 파일명
            directory (str, optional): 저장할 디렉토리 경로

        Returns:
            str: 저장된 파일의 전체 경로
        """
        try:
            # 데이터 정제
            df = self.clean_data(data)

            if df.empty:
                logger.warning("내보낼 데이터가 없습니다.")
                return None

            # 저장 디렉토리 설정
            save_dir = directory if directory else self.default_directory
            os.makedirs(save_dir, exist_ok=True)

            # 파일명 설정 (지정되지 않은 경우 현재 날짜와 시간 사용)
            if not filename:
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"부동산_중개사무소_{current_time}.csv"

            # 확장자 확인 및 추가
            if not filename.lower().endswith('.csv'):
                filename += '.csv'

            # 전체 파일 경로
            file_path = os.path.join(save_dir, filename)

            # CSV 파일로 저장 (한글 깨짐 방지를 위해 UTF-8 with BOM 사용)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')

            logger.info(f"CSV 파일 저장 완료: {file_path} ({len(df)}개 항목)")
            return file_path
        except Exception as e:
            logger.error(f"CSV 파일 저장 실패: {str(e)}")
            return None

    def get_default_directory(self):
        """기본 저장 디렉토리 반환"""
        return self.default_directory

    def set_default_directory(self, directory):
        """
        기본 저장 디렉토리 설정

        Args:
            directory (str): 설정할 디렉토리 경로

        Returns:
            bool: 설정 성공 여부
        """
        try:
            # 디렉토리 생성
            os.makedirs(directory, exist_ok=True)

            # 기본 디렉토리 업데이트
            self.default_directory = directory

            logger.info(f"기본 저장 디렉토리 설정: {directory}")
            return True
        except Exception as e:
            logger.error(f"기본 저장 디렉토리 설정 실패: {str(e)}")
            return False

# 테스트 코드
if __name__ == "__main__":
    # 테스트 데이터
    test_data = [
        {
            "시도": "서울특별시",
            "시군구": "강남구",
            "읍면동": "역삼동",
            "상호": "테스트부동산",
            "대표자명": "홍길동",
            "전화번호": "02-123-4567",
            "주소": "서울특별시 강남구 역삼동 123-45"
        },
        {
            "시도": "서울특별시",
            "시군구": "강남구",
            "읍면동": "역삼동",
            "상호": "샘플공인중개사",
            "대표자명": "김철수",
            "전화번호": "02-987-6543",
            "주소": "서울특별시 강남구 역삼동 456-78"
        }
    ]

    exporter = DataExporter()
    file_path = exporter.export_to_csv(test_data, "test_export.csv")

    if file_path:
        print(f"테스트 파일 저장 완료: {file_path}")
