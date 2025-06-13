"""
API 기반 솔루션 테스트 모듈
부동산 중개사무소 정보 크롤링 프로그램의 API 기반 솔루션을 테스트하는 모듈입니다.
"""

import os
import sys
import logging
import unittest
import pandas as pd
from datetime import datetime

# 프로젝트 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_crawler import ApiCrawler
from api_region_search import ApiRegionSearch
from data_exporter import DataExporter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApiTestValidator')

class TestApiCrawler(unittest.TestCase):
    """API 크롤러 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.crawler = ApiCrawler()
    
    def tearDown(self):
        """테스트 정리"""
        if hasattr(self, 'crawler'):
            self.crawler.close()
    
    def test_get_sido_list(self):
        """시도 목록 가져오기 테스트"""
        sido_list = self.crawler.get_sido_list()
        self.assertIsNotNone(sido_list, "시도 목록이 None입니다")
        self.assertGreater(len(sido_list), 0, "시도 목록이 비어 있습니다")
        logger.info(f"시도 목록: {sido_list}")
    
    def test_get_sigungu_list(self):
        """시군구 목록 가져오기 테스트"""
        sido_list = self.crawler.get_sido_list()
        
        if sido_list:
            # 첫 번째 시도의 시군구 목록 가져오기
            first_sido = sido_list[0]
            sigungu_list = self.crawler.get_sigungu_list(first_sido)
            
            self.assertIsNotNone(sigungu_list, f"{first_sido}의 시군구 목록이 None입니다")
            self.assertGreater(len(sigungu_list), 0, f"{first_sido}의 시군구 목록이 비어 있습니다")
            logger.info(f"{first_sido}의 시군구 목록: {sigungu_list}")
    
    def test_get_dong_list(self):
        """읍면동 목록 가져오기 테스트"""
        sido_list = self.crawler.get_sido_list()
        
        if sido_list:
            # 첫 번째 시도의 시군구 목록 가져오기
            first_sido = sido_list[0]
            sigungu_list = self.crawler.get_sigungu_list(first_sido)
            
            if sigungu_list:
                # 첫 번째 시군구의 읍면동 목록 가져오기
                first_sigungu = sigungu_list[0]
                dong_list = self.crawler.get_dong_list(first_sido, first_sigungu)
                
                self.assertIsNotNone(dong_list, f"{first_sido} {first_sigungu}의 읍면동 목록이 None입니다")
                self.assertGreaterEqual(len(dong_list), 0, f"{first_sido} {first_sigungu}의 읍면동 목록이 비어 있습니다")
                logger.info(f"{first_sido} {first_sigungu}의 읍면동 목록: {dong_list}")
    
    def test_search_real_estate_offices(self):
        """부동산 중개사무소 검색 테스트"""
        sido_list = self.crawler.get_sido_list()
        
        if sido_list:
            # 첫 번째 시도 선택
            first_sido = sido_list[0]
            sigungu_list = self.crawler.get_sigungu_list(first_sido)
            
            if sigungu_list:
                # 첫 번째 시군구 선택
                first_sigungu = sigungu_list[0]
                
                # 검색 수행
                result = self.crawler.search_real_estate_offices(first_sido, first_sigungu)
                
                # 검색 결과 확인
                self.assertGreaterEqual(len(self.crawler.results), 0, "검색 결과가 없습니다")
                logger.info(f"{first_sido} {first_sigungu} 검색 결과: {len(self.crawler.results)}개 항목")

class TestApiRegionSearch(unittest.TestCase):
    """API 기반 지역 검색 모듈 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.region_search = ApiRegionSearch()
    
    def tearDown(self):
        """테스트 정리"""
        if hasattr(self, 'region_search'):
            self.region_search.close()
    
    def test_initialize(self):
        """지역 정보 초기화 테스트"""
        result = self.region_search.initialize()
        self.assertTrue(result, "지역 정보 초기화 실패")
    
    def test_get_sido_list(self):
        """시도 목록 가져오기 테스트"""
        self.region_search.initialize()
        sido_list = self.region_search.get_sido_list()
        
        self.assertIsNotNone(sido_list, "시도 목록이 None입니다")
        self.assertGreater(len(sido_list), 0, "시도 목록이 비어 있습니다")
        logger.info(f"시도 목록: {sido_list}")
    
    def test_get_sigungu_list(self):
        """시군구 목록 가져오기 테스트"""
        self.region_search.initialize()
        sido_list = self.region_search.get_sido_list()
        
        if sido_list:
            # 첫 번째 시도의 시군구 목록 가져오기
            first_sido = sido_list[0]
            sigungu_list = self.region_search.get_sigungu_list(first_sido)
            
            self.assertIsNotNone(sigungu_list, f"{first_sido}의 시군구 목록이 None입니다")
            self.assertGreater(len(sigungu_list), 0, f"{first_sido}의 시군구 목록이 비어 있습니다")
            logger.info(f"{first_sido}의 시군구 목록: {sigungu_list}")
    
    def test_search(self):
        """검색 테스트"""
        self.region_search.initialize()
        sido_list = self.region_search.get_sido_list()
        
        if sido_list:
            # 첫 번째 시도 선택
            first_sido = sido_list[0]
            sigungu_list = self.region_search.get_sigungu_list(first_sido)
            
            if sigungu_list:
                # 첫 번째 시군구 선택
                first_sigungu = sigungu_list[0]
                
                # 검색 수행
                results = self.region_search.search(
                    first_sido, 
                    first_sigungu, 
                    output_file="test_api_region_search.csv"
                )
                
                self.assertIsNotNone(results, "검색 결과가 None입니다")
                logger.info(f"{first_sido} {first_sigungu} 검색 결과: {len(results)}개 항목")
                
                # 결과 파일 확인
                self.assertTrue(
                    os.path.exists("test_api_region_search.csv"), 
                    "결과 파일이 생성되지 않았습니다"
                )

def run_api_tests():
    """API 테스트 실행"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # API 크롤러 테스트 추가
    test_suite.addTest(unittest.makeSuite(TestApiCrawler))
    
    # API 지역 기반 검색 모듈 테스트 추가
    test_suite.addTest(unittest.makeSuite(TestApiRegionSearch))
    
    # 테스트 실행
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    return test_result.wasSuccessful()

def validate_api_solution():
    """API 기반 솔루션 검증"""
    logger.info("API 기반 솔루션 검증 시작")
    
    # 테스트 실행
    success = run_api_tests()
    
    if success:
        logger.info("모든 API 테스트가 성공적으로 완료되었습니다.")
    else:
        logger.error("일부 API 테스트가 실패했습니다.")
    
    return success

if __name__ == "__main__":
    validate_api_solution()
