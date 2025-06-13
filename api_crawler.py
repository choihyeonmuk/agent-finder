"""
API 기반 크롤러 모듈
부동산 중개사무소 정보 크롤링 프로그램의 API 기반 크롤러 모듈입니다.
웹드라이버 대신 API를 직접 호출하여 데이터를 수집합니다.
"""

import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple, Callable
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApiCrawler')

class ApiCrawler:
    """API 기반 크롤러 클래스"""

    def __init__(self):
        """크롤러 초기화"""
        self.base_url = "https://karhanbang.com/office"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://karhanbang.com/office/",
            "Connection": "keep-alive"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.results = []

        # 시도 코드 매핑 (웹사이트 분석 결과)
        self.sido_mapping = {
            "서울특별시": 1,
            "경기도": 2,
            "인천광역시": 3,
            "부산광역시": 4,
            "대구광역시": 5,
            "광주광역시": 6,
            "대전광역시": 7,
            "울산광역시": 8,
            "강원특별자치도": 9,
            "경상남도": 10,
            "경상북도": 11,
            "전라남도": 12,
            "전북특별자치도": 13,
            "충청남도": 14,
            "충청북도": 15,
            "세종특별자치시": 16,
            "제주특별자치도": 17
        }

        logger.info("API 크롤러 초기화 완료")

    def get_sido_list(self) -> List[str]:
        """
        시도 목록 가져오기

        Returns:
            List[str]: 시도 목록
        """
        # 시도 목록은 고정되어 있으므로 API 호출 없이 반환
        return list(self.sido_mapping.keys())

    def get_sigungu_list(self, sido: str) -> List[str]:
        """
        시군구 목록 가져오기

        Args:
            sido (str): 시도명

        Returns:
            List[str]: 시군구 목록
        """
        try:
            # 시도 코드 가져오기
            sido_code = self.sido_mapping.get(sido)
            if not sido_code:
                logger.error(f"시도 코드를 찾을 수 없음: {sido}")
                return []

            # API 호출을 위한 타임스탬프 생성
            timestamp = int(time.time() * 1000)

            # API 호출
            url = f"{self.base_url}/ajax_combo_search.asp"
            params = {
                "flag": "S",
                "sel_sido": sido_code,
                "sel_gugun": "",
                "sel_dong": "",
                "search": "",
                "_": timestamp
            }

            response = self.session.get(url, params=params)

            # 응답 확인
            if response.status_code != 200:
                logger.error(f"시군구 목록 가져오기 실패: {response.status_code}")
                return []

            # JSON 파싱
            data = response.json()

            # 시군구 목록 추출
            if "datMM" in data and "name" in data["datMM"]:
                sigungu_list = data["datMM"]["name"]
                # 유니코드 이스케이프 시퀀스 디코딩 - 개선된 인코딩 처리
                sigungu_list = [name.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') for name in sigungu_list]
                logger.info(f"{sido}의 시군구 목록 가져오기 성공: {len(sigungu_list)}개")

                # 시군구 코드 매핑 저장
                self.sigungu_codes = {}
                if "code" in data["datMM"]:
                    for i, code in enumerate(data["datMM"]["code"]):
                        if i < len(sigungu_list):
                            self.sigungu_codes[sigungu_list[i]] = code

                return sigungu_list
            else:
                logger.error("시군구 목록 데이터 형식 오류")
                return []

        except Exception as e:
            logger.error(f"시군구 목록 가져오기 중 오류 발생: {str(e)}")
            return []

    def get_dong_list(self, sido: str, sigungu: str) -> List[str]:
        """
        읍면동 목록 가져오기

        Args:
            sido (str): 시도명
            sigungu (str): 시군구명

        Returns:
            List[str]: 읍면동 목록
        """
        try:
            # 시도 코드 가져오기
            sido_code = self.sido_mapping.get(sido)
            if not sido_code:
                logger.error(f"시도 코드를 찾을 수 없음: {sido}")
                return []

            # 시군구 코드 가져오기
            sigungu_code = self.sigungu_codes.get(sigungu)
            if not sigungu_code:
                logger.error(f"시군구 코드를 찾을 수 없음: {sigungu}")
                return []

            # API 호출을 위한 타임스탬프 생성
            timestamp = int(time.time() * 1000)

            # API 호출
            url = f"{self.base_url}/ajax_combo_search.asp"
            params = {
                "flag": "G",
                "sel_sido": sido_code,
                "sel_gugun": sigungu_code,
                "sel_dong": "",
                "search": "",
                "_": timestamp
            }

            response = self.session.get(url, params=params)

            # 응답 확인
            if response.status_code != 200:
                logger.error(f"읍면동 목록 가져오기 실패: {response.status_code}")
                return []

            # JSON 파싱
            data = response.json()

            # 읍면동 목록 추출
            if "datMM" in data and "name" in data["datMM"]:
                dong_list = data["datMM"]["name"]
                # 유니코드 이스케이프 시퀀스 디코딩 - 개선된 인코딩 처리
                dong_list = [name.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') for name in dong_list]
                logger.info(f"{sido} {sigungu}의 읍면동 목록 가져오기 성공: {len(dong_list)}개")

                # 읍면동 코드 매핑 저장
                self.dong_codes = {}
                if "code" in data["datMM"]:
                    for i, code in enumerate(data["datMM"]["code"]):
                        if i < len(dong_list):
                            self.dong_codes[dong_list[i]] = code

                return dong_list
            else:
                logger.error("읍면동 목록 데이터 형식 오류")
                return []

        except Exception as e:
            logger.error(f"읍면동 목록 가져오기 중 오류 발생: {str(e)}")
            return []

    def get_total_pages(self, sido_code: int, sigungu_code: Optional[int] = None, dong_code: str = "") -> int:
        """
        검색 결과의 총 페이지 수 가져오기

        Args:
            sido_code (int): 시도 코드
            sigungu_code (Optional[int]): 시군구 코드 (선택)
            dong_code (str): 읍면동 코드 (선택)

        Returns:
            int: 총 페이지 수
        """
        try:
            # 검색 페이지 URL
            url = f"{self.base_url}/office_list.asp"

            # 검색 파라미터
            params = {
                "topM": "09",
                "flag": "S",
                "page": 1,
                "search": "",
                "sel_sido": sido_code
            }

            if sigungu_code:
                params["sel_gugun"] = sigungu_code

            if dong_code:
                params["sel_dong"] = dong_code

            # 페이지 요청
            response = self.session.get(url, params=params)

            # 응답 확인
            if response.status_code != 200:
                logger.error(f"부동산 중개사무소 페이지 가져오기 실패: {response.status_code}")
                return 0

            # HTML 파싱
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # 페이지네이션 링크 찾기
            pagination_links = soup.select('.pagination a, a[href*="page="]')
            if pagination_links:
                # 페이지네이션에서 마지막 페이지 번호 추출
                try:
                    # '>>' 링크에서 마지막 페이지 번호 추출
                    last_page_link = None
                    for link in pagination_links:
                        if link.text.strip() == '>>' or link.text.strip() == '»':
                            last_page_link = link.get('href')
                            break

                    if last_page_link:
                        # URL에서 page 파라미터 추출
                        import re
                        page_match = re.search(r'page=(\d+)', last_page_link)
                        if page_match:
                            return int(page_match.group(1))

                    # 숫자 페이지 링크에서 최대 페이지 번호 추출
                    page_numbers = [int(a.text.strip()) for a in pagination_links if a.text.strip().isdigit()]
                    if page_numbers:
                        return max(page_numbers)
                except Exception as e:
                    logger.error(f"페이지 수 추출 중 오류 발생: {str(e)}")

            return 1  # 기본값 1페이지

        except Exception as e:
            logger.error(f"총 페이지 수 가져오기 중 오류 발생: {str(e)}")
            return 1  # 오류 발생 시 기본값 1페이지

    def search_real_estate_offices(self, sido: str, sigungu: Optional[str] = None, dong: Optional[str] = None, progress_callback=None) -> bool:
        """
        부동산 중개사무소 검색

        Args:
            sido (str): 시도명
            sigungu (Optional[str]): 시군구명 (선택)
            dong (Optional[str]): 읍면동명 (선택)
            progress_callback (Optional[Callable]): 진행 상황 콜백 함수

        Returns:
            bool: 검색 성공 여부
        """
        try:
            # 시도 코드 가져오기
            sido_code = self.sido_mapping.get(sido)
            if not sido_code:
                logger.error(f"시도 코드를 찾을 수 없음: {sido}")
                return False

            # 시군구 코드 가져오기
            sigungu_code = None
            if sigungu:
                if not hasattr(self, 'sigungu_codes'):
                    self.get_sigungu_list(sido)

                sigungu_code = self.sigungu_codes.get(sigungu)
                if not sigungu_code:
                    logger.error(f"시군구 코드를 찾을 수 없음: {sigungu}")
                    return False

            # 읍면동 코드 가져오기
            dong_code = ""
            if dong and sigungu:
                if not hasattr(self, 'dong_codes'):
                    self.get_dong_list(sido, sigungu)

                dong_code = self.dong_codes.get(dong, "")

            # 총 페이지 수 가져오기
            total_pages = self.get_total_pages(sido_code, sigungu_code, dong_code)
            logger.info(f"총 페이지 수: {total_pages}")

            # 진행 상황 콜백 호출 (총 페이지 수 전달)
            if progress_callback:
                progress_callback(0, total_pages, 0)

            # 웹페이지에서 데이터 가져오기
            self.results = self._scrape_office_data_from_html(sido_code, sigungu_code, dong_code, progress_callback)

            # 상세 정보 업데이트
            for result in self.results:
                if result.get('mem_no'):
                    try:
                        detail_url = f"{self.base_url}/office_detail.asp?mem_no={result['mem_no']}"
                        detail_response = self.session.get(detail_url)
                        if detail_response.status_code == 200:
                            from bs4 import BeautifulSoup
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

                            # 모든 전화번호 추출
                            phone_elements = detail_soup.find_all(text=re.compile(r'(\d{2,3}-\d{3,4}-\d{4}|010-\d{4}-\d{4})'))
                            mobile_phones = []
                            for phone_element in phone_elements:
                                phone = phone_element.strip()
                                if phone not in mobile_phones:  # 중복 제거
                                    mobile_phones.append(phone)

                            # 모바일 전화번호 업데이트
                            result['모바일전화번호'] = ", ".join(mobile_phones)

                            # 추가 정보 추출 가능한 경우 여기에 추가
                            # 예: 이메일, 팩스, 영업시간 등

                    except Exception as e:
                        logger.error(f"상세 정보 업데이트 중 오류 발생: {str(e)}")
                        continue

            return len(self.results) > 0

        except Exception as e:
            logger.error(f"부동산 중개사무소 검색 중 오류 발생: {str(e)}")
            return False

    def _scrape_office_data_from_html(self, sido_code: int, sigungu_code: Optional[int] = None, dong_code: str = "", progress_callback=None) -> List[Dict[str, Any]]:
        """
        HTML에서 부동산 중개사무소 데이터 스크래핑

        Args:
            sido_code (int): 시도 코드
            sigungu_code (Optional[int]): 시군구 코드 (선택)
            dong_code (str): 읍면동 코드 (선택)
            progress_callback (Optional[Callable]): 진행 상황 콜백 함수

        Returns:
            List[Dict[str, Any]]: 부동산 중개사무소 데이터 목록
        """
        try:
            # 검색 페이지 URL - 직접 office_list.asp 페이지 호출
            url = f"{self.base_url}/office_list.asp"

            # 검색 파라미터
            params = {
                "topM": "09",
                "flag": "S",
                "page": 1,
                "search": "",
                "sel_sido": sido_code
            }

            if sigungu_code:
                params["sel_gugun"] = sigungu_code

            if dong_code:
                params["sel_dong"] = dong_code

            # 페이지 요청
            response = self.session.get(url, params=params)

            # 응답 확인
            if response.status_code != 200:
                logger.error(f"부동산 중개사무소 페이지 가져오기 실패: {response.status_code}")
                return []

            # HTML 파싱 및 데이터 추출
            from bs4 import BeautifulSoup

            # 결과 저장 리스트
            results = []

            # 현재 페이지 번호
            current_page = 1
            total_pages = 1  # 초기값, 실제 페이지 수는 첫 페이지에서 확인

            # 모든 페이지 순회
            while current_page <= total_pages:
                # 진행 상황 콜백 호출
                if progress_callback:
                    progress_callback(current_page, total_pages, len(results))

                # 페이지 파라미터 추가
                page_params = params.copy()
                page_params['page'] = current_page

                # 페이지 요청
                if current_page > 1:
                    page_response = self.session.get(url, params=page_params)
                    if page_response.status_code != 200:
                        logger.error(f"페이지 {current_page} 가져오기 실패: {page_response.status_code}")
                        break
                    soup = BeautifulSoup(page_response.text, 'html.parser')
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')

                # 첫 페이지에서 총 페이지 수 확인
                if current_page == 1:
                    # 페이지네이션 링크 찾기
                    pagination_links = soup.select('.pagination a, a[href*="page="]')
                    if pagination_links:
                        # 페이지네이션에서 마지막 페이지 번호 추출
                        try:
                            # 숫자 페이지 링크에서 페이지 번호 추출
                            page_numbers = [int(a.text.strip()) for a in pagination_links if a.text.strip().isdigit()]

                            # '>>' 링크에서 마지막 페이지 번호 추출 (더 정확함)
                            last_page_link = None
                            for link in pagination_links:
                                if link.text.strip() == '>>' or link.text.strip() == '»':
                                    last_page_link = link.get('href')
                                    break

                            if last_page_link:
                                # URL에서 page 파라미터 추출
                                import re
                                page_match = re.search(r'page=(\d+)', last_page_link)
                                if page_match:
                                    last_page = int(page_match.group(1))
                                    total_pages = last_page
                            elif page_numbers:
                                total_pages = max(page_numbers)
                        except Exception as e:
                            logger.error(f"페이지 수 추출 중 오류 발생: {str(e)}")

                    logger.info(f"총 페이지 수: {total_pages}")

                # 테이블에서 데이터 추출 - 테이블 구조에 맞게 수정
                office_rows = soup.select('table tr')

                # 헤더 행 건너뛰기
                for row in office_rows[1:]:
                    try:
                        # 각 컬럼에서 데이터 추출
                        columns = row.select('td')

                        if len(columns) >= 5:  # 최소 5개 컬럼 필요
                            # 지역 (첫 번째 컬럼)
                            location = columns[0].text.strip()

                            # 상호명 (두 번째 컬럼)
                            office_name_elem = columns[1].select_one('a')
                            if office_name_elem:
                                raw_name = office_name_elem.text.strip()
                                name_lines = raw_name.splitlines()
                                office_name = name_lines[0].strip() if name_lines else ""

                                # mem_no 추출
                                href = office_name_elem.get('href', '')
                                mem_no_match = re.search(r"moveDetail\('(\d+)',", href)
                                if mem_no_match:
                                    mem_no = mem_no_match.group(1)
                                else:
                                    mem_no = None

                                print('mem_no:', mem_no)  # mem_no 값 확인

                            else:
                                office_name = ""
                                mem_no = None

                            # 대표자명 (세 번째 컬럼)
                            representative = columns[2].text.strip()

                            # 전화번호 (네 번째 컬럼)
                            phone_elem = columns[3].select_one('a')
                            phone = phone_elem.text.strip() if phone_elem else ""

                            # 주소 (다섯 번째 컬럼)
                            address = columns[4].text.strip()

                            # 상세 페이지에서 연락처 가져오기
                            mobile_phones = []
                            if mem_no:
                                try:
                                    detail_url = f"{self.base_url}/office_detail.asp?mem_no={mem_no}"
                                    detail_response = self.session.get(detail_url)
                                    if detail_response.status_code == 200:
                                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                        # 모든 전화번호 요소 찾기
                                        phone_elements = detail_soup.find_all(text=re.compile(r'(\d{2,3}-\d{3,4}-\d{4}|010-\d{4}-\d{4})'))
                                        for phone_element in phone_elements:
                                            phone = phone_element.strip()
                                            if phone not in mobile_phones:  # 중복 제거
                                                mobile_phones.append(phone)
                                except Exception as e:
                                    logger.error(f"상세 페이지에서 연락처 추출 중 오류 발생: {str(e)}")

                            # 결과 추가
                            office_data = {
                                "시도": self._get_sido_name_by_code(sido_code),
                                "시군구": self._get_sigungu_name_by_code(sigungu_code) if sigungu_code else "",
                                "읍면동": self._get_dong_name_by_code(dong_code) if dong_code else "",
                                "지역": location,
                                "상호": office_name,
                                "대표자명": representative,
                                "전화번호": phone,
                                "모바일전화번호": ", ".join(mobile_phones),  # 모든 연락처를 쉼표로 구분하여 저장
                                "주소": address,
                                "mem_no": mem_no
                            }

                            results.append(office_data)

                    except Exception as e:
                        logger.error(f"데이터 추출 중 오류 발생: {str(e)}")
                        continue

                logger.info(f"페이지 {current_page}/{total_pages} 처리 완료, 현재까지 {len(results)}개 항목 추출")

                # 다음 페이지로 이동
                current_page += 1

            logger.info(f"부동산 중개사무소 데이터 추출 성공: 총 {len(results)}개")
            return results

        except Exception as e:
            logger.error(f"HTML에서 데이터 스크래핑 중 오류 발생: {str(e)}")
            return []

    def _get_sido_name_by_code(self, code: int) -> str:
        """
        시도 코드로 시도명 가져오기

        Args:
            code (int): 시도 코드

        Returns:
            str: 시도명
        """
        for sido, sido_code in self.sido_mapping.items():
            if sido_code == code:
                return sido
        return ""

    def _get_sigungu_name_by_code(self, code: int) -> str:
        """
        시군구 코드로 시군구명 가져오기

        Args:
            code (int): 시군구 코드

        Returns:
            str: 시군구명
        """
        if hasattr(self, 'sigungu_codes'):
            for sigungu, sigungu_code in self.sigungu_codes.items():
                if sigungu_code == code:
                    return sigungu
        return ""

    def _get_dong_name_by_code(self, code: str) -> str:
        """
        읍면동 코드로 읍면동명 가져오기

        Args:
            code (str): 읍면동 코드

        Returns:
            str: 읍면동명
        """
        if hasattr(self, 'dong_codes'):
            for dong, dong_code in self.dong_codes.items():
                if dong_code == code:
                    return dong
        return ""

    def get_results(self) -> List[Dict[str, Any]]:
        """
        검색 결과 가져오기

        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        return self.results

    def close(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            logger.info("세션 종료")

# 테스트 코드
if __name__ == "__main__":
    # API 크롤러 생성
    crawler = ApiCrawler()

    try:
        # 시도 목록 가져오기
        sido_list = crawler.get_sido_list()
        print(f"시도 목록: {sido_list}")

        if sido_list:
            # 첫 번째 시도의 시군구 목록 가져오기
            first_sido = sido_list[0]
            sigungu_list = crawler.get_sigungu_list(first_sido)
            print(f"{first_sido}의 시군구 목록: {sigungu_list}")

            if sigungu_list:
                # 첫 번째 시군구의 읍면동 목록 가져오기
                first_sigungu = sigungu_list[0]
                dong_list = crawler.get_dong_list(first_sido, first_sigungu)
                print(f"{first_sido} {first_sigungu}의 읍면동 목록: {dong_list}")

                # 부동산 중개사무소 검색
                success = crawler.search_real_estate_offices(first_sido, first_sigungu)

                if success:
                    # 검색 결과 출력
                    results = crawler.get_results()
                    print(f"검색 결과: {len(results)}개")

                    for i, result in enumerate(results[:5]):  # 처음 5개만 출력
                        print(f"결과 {i+1}: {result}")
                else:
                    print("검색 실패")

    finally:
        # 세션 종료
        crawler.close()
