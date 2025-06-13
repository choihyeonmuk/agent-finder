"""
API 기반 지역 검색 모듈
부동산 중개사무소 정보 크롤링 프로그램의 API 기반 지역 검색 모듈입니다.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# 프로젝트 모듈 임포트
from api_crawler import ApiCrawler
from data_exporter import DataExporter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApiRegionSearch')

class ApiRegionSearch:
    """API 기반 지역 검색 클래스"""

    def __init__(self):
        """검색 모듈 초기화"""
        self.api_crawler = ApiCrawler()
        self.data_exporter = DataExporter()
        self.sido_list = []
        self.sigungu_list = {}
        self.dong_list = {}

        logger.info("API 기반 지역 검색 모듈 초기화 완료")

    def initialize(self) -> bool:
        """
        지역 정보 초기화

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 시도 목록 가져오기
            self.sido_list = self.api_crawler.get_sido_list()

            if not self.sido_list:
                logger.error("시도 목록 가져오기 실패")
                return False

            logger.info(f"지역 정보 초기화 완료: {len(self.sido_list)}개 시도")
            return True

        except Exception as e:
            logger.error(f"지역 정보 초기화 중 오류 발생: {str(e)}")
            return False

    def get_sido_list(self) -> List[str]:
        """
        시도 목록 가져오기

        Returns:
            List[str]: 시도 목록
        """
        return self.sido_list

    def get_sigungu_list(self, sido: str) -> List[str]:
        """
        시군구 목록 가져오기

        Args:
            sido (str): 시도명

        Returns:
            List[str]: 시군구 목록
        """
        # 캐시된 데이터가 있는지 확인
        if sido in self.sigungu_list:
            return self.sigungu_list[sido]

        # API를 통해 시군구 목록 가져오기
        sigungu_list = self.api_crawler.get_sigungu_list(sido)

        # 캐시에 저장
        self.sigungu_list[sido] = sigungu_list

        return sigungu_list

    def get_dong_list(self, sido: str, sigungu: str) -> List[str]:
        """
        읍면동 목록 가져오기

        Args:
            sido (str): 시도명
            sigungu (str): 시군구명

        Returns:
            List[str]: 읍면동 목록
        """
        # 캐시 키 생성
        cache_key = f"{sido}_{sigungu}"

        # 캐시된 데이터가 있는지 확인
        if cache_key in self.dong_list:
            return self.dong_list[cache_key]

        # API를 통해 읍면동 목록 가져오기
        dong_list = self.api_crawler.get_dong_list(sido, sigungu)

        # 캐시에 저장
        self.dong_list[cache_key] = dong_list

        return dong_list

    def search(self, sido: str, sigungu: Optional[str] = None, dong: Optional[str] = None, output_file: Optional[str] = None, progress_callback=None) -> List[Dict[str, Any]]:
        """
        부동산 중개사무소 검색

        Args:
            sido (str): 시도명
            sigungu (Optional[str]): 시군구명 (선택)
            dong (Optional[str]): 읍면동명 (선택)
            output_file (Optional[str]): 출력 파일명 (선택)
            progress_callback (Optional[callable]): 진행 상황 업데이트 콜백 함수

        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            logger.info(f"검색 시작: {sido} {sigungu} {dong if dong else ''}")

            # 부동산 중개사무소 검색
            success = self.api_crawler.search_real_estate_offices(sido, sigungu, dong, progress_callback)

            if not success:
                logger.error("검색 실패")
                return []

            # 검색 결과 가져오기
            results = self.api_crawler.get_results()

            logger.info(f"검색 결과: {len(results)}개")

            # 결과를 파일로 저장
            if output_file and results:
                file_path = self.data_exporter.export_to_csv(results, output_file)
                logger.info(f"검색 결과 저장 완료: {file_path}")

            return results

        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            return []

    def close(self):
        """리소스 정리"""
        if hasattr(self, 'api_crawler'):
            self.api_crawler.close()
            logger.info("API 크롤러 종료")

# 테스트 코드
if __name__ == "__main__":
    # 지역 검색 모듈 생성
    region_search = ApiRegionSearch()

    try:
        # 지역 정보 초기화
        if region_search.initialize():
            # 시도 목록 출력
            sido_list = region_search.get_sido_list()
            print(f"시도 목록: {sido_list}")

            if sido_list:
                # 첫 번째 시도의 시군구 목록 출력
                first_sido = sido_list[0]
                sigungu_list = region_search.get_sigungu_list(first_sido)
                print(f"{first_sido}의 시군구 목록: {sigungu_list}")

                if sigungu_list:
                    # 첫 번째 시군구의 읍면동 목록 출력
                    first_sigungu = sigungu_list[0]
                    dong_list = region_search.get_dong_list(first_sido, first_sigungu)
                    print(f"{first_sido} {first_sigungu}의 읍면동 목록: {dong_list}")

                    # 검색 수행
                    results = region_search.search(
                        first_sido,
                        first_sigungu,
                        output_file="test_api_region_search.csv"
                    )

                    # 검색 결과 출력
                    print(f"검색 결과: {len(results)}개")

                    for i, result in enumerate(results[:5]):  # 처음 5개만 출력
                        print(f"결과 {i+1}: {result}")

    finally:
        # 리소스 정리
        region_search.close()
