"""
API 기반 GUI 모듈
부동산 중개사무소 정보 크롤링 프로그램의 API 기반 GUI 모듈입니다.
"""

import os
import sys
import logging
import threading
import time
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QProgressBar,
    QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent, QObject, pyqtSignal

# 프로젝트 모듈 임포트
from api_region_search import ApiRegionSearch
from data_exporter import DataExporter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApiGUI')

class ApiSearchWorker(threading.Thread):
    """API 검색 워커 스레드"""

    def __init__(self, region_search, sido, sigungu, dong=None, progress_callback=None):
        """
        워커 초기화

        Args:
            region_search (ApiRegionSearch): 지역 검색 객체
            sido (str): 시도명
            sigungu (str): 시군구명
            dong (Optional[str]): 읍면동명 (선택)
            progress_callback (Optional[callable]): 진행 상황 업데이트 콜백 함수
        """
        super().__init__()
        self.region_search = region_search
        self.sido = sido
        self.sigungu = sigungu
        self.dong = dong
        self.results = []
        self.daemon = True
        self._stop_event = threading.Event()
        self.progress_callback = progress_callback

    def run(self):
        """스레드 실행"""
        try:
            # 검색 수행
            self.results = self.region_search.search(
                self.sido,
                self.sigungu,
                self.dong,
                progress_callback=self.progress_callback
            )
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            self.results = []

    def stop(self):
        """스레드 중지"""
        self._stop_event.set()

    def stopped(self):
        """스레드 중지 여부 확인"""
        return self._stop_event.is_set()

class ApiRealEstateGUI(QMainWindow):
    """API 기반 부동산 중개사무소 정보 크롤링 GUI 클래스"""

    def __init__(self):
        """GUI 초기화"""
        super().__init__()

        # 창 제목 및 크기 설정
        self.setWindowTitle("중개찾기(AgentFinder)")
        self.setGeometry(100, 100, 1000, 600)

        # 지역 검색 모듈 초기화
        self.region_search = ApiRegionSearch()
        self.data_exporter = DataExporter()

        # 검색 결과 저장
        self.search_results = []

        # UI 초기화
        self._init_ui()

        # 지역 정보 초기화
        self._initialize_region_data()

        logger.info("GUI 초기화 완료")

    def _init_ui(self):
        """UI 초기화"""
        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃 설정
        main_layout = QVBoxLayout(central_widget)

        # 검색 영역 생성
        search_layout = QVBoxLayout()

        # 지역 선택 영역
        region_layout = QHBoxLayout()

        # 시도 선택
        sido_layout = QVBoxLayout()
        sido_label = QLabel("시/도")
        self.sido_combo = QComboBox()
        self.sido_combo.currentIndexChanged.connect(self._on_sido_changed)
        sido_layout.addWidget(sido_label)
        sido_layout.addWidget(self.sido_combo)

        # 시군구 선택
        sigungu_layout = QVBoxLayout()
        sigungu_label = QLabel("시/군/구")
        self.sigungu_combo = QComboBox()
        self.sigungu_combo.currentIndexChanged.connect(self._on_sigungu_changed)
        sigungu_layout.addWidget(sigungu_label)
        sigungu_layout.addWidget(self.sigungu_combo)

        # 읍면동 선택
        dong_layout = QVBoxLayout()
        dong_label = QLabel("읍/면/동")
        self.dong_combo = QComboBox()
        dong_layout.addWidget(dong_label)
        dong_layout.addWidget(self.dong_combo)

        # 지역 선택 영역에 추가
        region_layout.addLayout(sido_layout)
        region_layout.addLayout(sigungu_layout)
        region_layout.addLayout(dong_layout)

        # 버튼 영역
        button_layout = QHBoxLayout()

        # 검색 버튼
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self._on_search_clicked)

        # 초기화 버튼
        self.reset_button = QPushButton("초기화")
        self.reset_button.clicked.connect(self._on_reset_clicked)

        # CSV 내보내기 버튼
        self.export_button = QPushButton("CSV 저장")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)

        # 버튼 영역에 추가
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.export_button)

        # 검색 영역에 추가
        search_layout.addLayout(region_layout)
        search_layout.addLayout(button_layout)

        # 진행 상황 표시
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # 작업 상태 표시
        status_layout = QVBoxLayout()
        self.status_label = QLabel("준비")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)

        # 페이지 진행 상황 표시
        self.page_progress_label = QLabel("페이지: 0/0")
        self.page_progress_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.page_progress_label)

        # 작업 결과 표시
        result_info_layout = QHBoxLayout()
        self.result_count_label = QLabel("검색 결과: 0개")
        self.result_count_label.setAlignment(Qt.AlignLeft)
        self.result_time_label = QLabel("소요 시간: 0초")
        self.result_time_label.setAlignment(Qt.AlignRight)
        result_info_layout.addWidget(self.result_count_label)
        result_info_layout.addWidget(self.result_time_label)

        # 결과 테이블
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels([
            "시도", "시군구", "읍면동", "상호", "대표자명",
            "전화번호", "모바일전화번호", "주소"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 상태 표시줄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

        # 메인 레이아웃에 추가
        main_layout.addLayout(search_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(status_layout)
        main_layout.addLayout(result_info_layout)
        main_layout.addWidget(self.result_table)

        # 이벤트 필터 설치
        self.installEventFilter(self)

    def _initialize_region_data(self):
        """지역 정보 초기화"""
        try:
            # 진행 상황 업데이트
            self.status_bar.showMessage("지역 정보 초기화 중...")
            self.progress_bar.setValue(10)

            # 지역 정보 초기화
            success = self.region_search.initialize()

            if not success:
                self.status_bar.showMessage("지역 정보 초기화 실패")
                self.progress_bar.setValue(0)
                QMessageBox.critical(self, "초기화 실패", "지역 정보를 가져오는데 실패했습니다.")
                return

            # 시도 목록 가져오기
            sido_list = self.region_search.get_sido_list()

            # 시도 콤보박스 업데이트
            self.sido_combo.clear()
            self.sido_combo.addItems(sido_list)

            # 진행 상황 업데이트
            self.status_bar.showMessage("지역 정보 초기화 완료")
            self.progress_bar.setValue(100)

        except Exception as e:
            logger.error(f"지역 정보 초기화 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("지역 정보 초기화 실패")
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "초기화 실패", f"지역 정보를 가져오는데 실패했습니다: {str(e)}")

    def _on_sido_changed(self, index):
        """
        시도 선택 변경 이벤트 처리

        Args:
            index (int): 선택된 인덱스
        """
        try:
            if index < 0:
                return

            # 선택된 시도 가져오기
            sido = self.sido_combo.currentText()

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"{sido}의 시군구 정보 가져오는 중...")
            self.progress_bar.setValue(10)

            # 시군구 목록 가져오기
            sigungu_list = self.region_search.get_sigungu_list(sido)

            # 시군구 콤보박스 업데이트
            self.sigungu_combo.clear()
            self.sigungu_combo.addItems(sigungu_list)

            # 읍면동 콤보박스 초기화
            self.dong_combo.clear()

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"{sido}의 시군구 정보 가져오기 완료")
            self.progress_bar.setValue(100)

        except Exception as e:
            logger.error(f"시도 변경 처리 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("시군구 정보 가져오기 실패")
            self.progress_bar.setValue(0)

    def _on_sigungu_changed(self, index):
        """
        시군구 선택 변경 이벤트 처리

        Args:
            index (int): 선택된 인덱스
        """
        try:
            if index < 0:
                return

            # 선택된 시도와 시군구 가져오기
            sido = self.sido_combo.currentText()
            sigungu = self.sigungu_combo.currentText()

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"{sido} {sigungu}의 읍면동 정보 가져오는 중...")
            self.progress_bar.setValue(10)

            # 읍면동 목록 가져오기
            dong_list = self.region_search.get_dong_list(sido, sigungu)

            # 읍면동 콤보박스 업데이트
            self.dong_combo.clear()
            self.dong_combo.addItem("전체")
            self.dong_combo.addItems(dong_list)

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"{sido} {sigungu}의 읍면동 정보 가져오기 완료")
            self.progress_bar.setValue(100)

        except Exception as e:
            logger.error(f"시군구 변경 처리 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("읍면동 정보 가져오기 실패")
            self.progress_bar.setValue(0)

    def _on_search_clicked(self):
        """검색 버튼 클릭 이벤트 처리"""
        try:
            # 선택된 지역 정보 가져오기
            sido = self.sido_combo.currentText()
            sigungu = self.sigungu_combo.currentText()
            dong = self.dong_combo.currentText() if self.dong_combo.currentIndex() > 0 else None

            # 검색 조건 확인
            if not sido or not sigungu:
                QMessageBox.warning(self, "검색 조건 부족", "시/도와 시/군/구를 선택해주세요.")
                return

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"{sido} {sigungu} {dong if dong else ''} 검색 중...")
            self.status_label.setText(f"{sido} {sigungu} {dong if dong else ''} 검색 중...")
            self.progress_bar.setValue(10)

            # 버튼 비활성화
            self.search_button.setEnabled(False)
            self.export_button.setEnabled(False)

            # 검색 시작 시간 기록
            self.search_start_time = time.time()

            # 검색 워커 스레드 생성 및 시작
            self.search_worker = ApiSearchWorker(
                self.region_search,
                sido,
                sigungu,
                dong,
                progress_callback=self._update_page_progress
            )
            self.search_worker.start()

            # 검색 결과 확인 타이머 시작
            self._check_search_results()

        except Exception as e:
            logger.error(f"검색 처리 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("검색 실패")
            self.status_label.setText("검색 실패")
            self.progress_bar.setValue(0)
            self.search_button.setEnabled(True)
            QMessageBox.critical(self, "검색 실패", f"검색 중 오류가 발생했습니다: {str(e)}")

    def _check_search_results(self):
        """검색 결과 확인"""
        if self.search_worker.is_alive():
            # 아직 검색 중
            self.progress_bar.setValue(50)
            QApplication.processEvents()
            # 100ms 후 다시 확인
            self.status_bar.showMessage(f"검색 중... 잠시만 기다려주세요.")
            QApplication.instance().processEvents()
            QApplication.instance().postEvent(
                self,
                CheckSearchResultsEvent()
            )
        else:
            # 검색 완료
            self._process_search_results()

    def _process_search_results(self):
        """검색 결과 처리"""
        try:
            # 검색 결과 가져오기
            self.search_results = self.search_worker.results

            # 결과 테이블 초기화
            self.result_table.setRowCount(0)

            if not self.search_results:
                # 검색 결과 없음
                self.status_bar.showMessage("검색 결과가 없습니다.")
                self.status_label.setText("검색 결과가 없습니다.")
                self.progress_bar.setValue(0)
                self.search_button.setEnabled(True)
                QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
                return

            # 결과 테이블에 데이터 추가
            self.result_table.setRowCount(len(self.search_results))

            for row, data in enumerate(self.search_results):
                self.result_table.setItem(row, 0, QTableWidgetItem(data.get("시도", "")))
                self.result_table.setItem(row, 1, QTableWidgetItem(data.get("시군구", "")))
                self.result_table.setItem(row, 2, QTableWidgetItem(data.get("읍면동", "")))
                self.result_table.setItem(row, 3, QTableWidgetItem(data.get("상호", "")))
                self.result_table.setItem(row, 4, QTableWidgetItem(data.get("대표자명", "")))
                self.result_table.setItem(row, 5, QTableWidgetItem(data.get("전화번호", "")))
                self.result_table.setItem(row, 6, QTableWidgetItem(data.get("모바일전화번호", "")))
                self.result_table.setItem(row, 7, QTableWidgetItem(data.get("주소", "")))

            # 검색 소요 시간 계산
            search_time = time.time() - self.search_start_time

            # 진행 상황 업데이트
            self.status_bar.showMessage(f"검색 완료: {len(self.search_results)}개 결과")
            self.status_label.setText("검색 완료!")
            self.progress_bar.setValue(100)
            self.result_count_label.setText(f"검색 결과: {len(self.search_results)}개")
            self.result_time_label.setText(f"소요 시간: {search_time:.1f}초")

            # 버튼 활성화
            self.search_button.setEnabled(True)
            self.export_button.setEnabled(True)

            # 결과 메시지 표시
            QMessageBox.information(self, "검색 완료", f"{len(self.search_results)}개의 부동산 중개사무소를 찾았습니다.")

        except Exception as e:
            logger.error(f"검색 결과 처리 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("검색 결과 처리 실패")
            self.status_label.setText("검색 결과 처리 실패")
            self.progress_bar.setValue(0)
            self.search_button.setEnabled(True)
            QMessageBox.critical(self, "검색 결과 처리 실패", f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}")

    def _on_reset_clicked(self):
        """초기화 버튼 클릭 이벤트 처리"""
        try:
            # 콤보박스 초기화
            self.sido_combo.setCurrentIndex(0)
            self.sigungu_combo.clear()
            self.dong_combo.clear()

            # 결과 테이블 초기화
            self.result_table.setRowCount(0)

            # 검색 결과 초기화
            self.search_results = []

            # 버튼 상태 초기화
            self.search_button.setEnabled(True)
            self.export_button.setEnabled(False)

            # 진행 상황 초기화
            self.status_bar.showMessage("초기화 완료")
            self.progress_bar.setValue(0)

        except Exception as e:
            logger.error(f"초기화 중 오류 발생: {str(e)}")
            self.status_bar.showMessage("초기화 실패")

    def _on_export_clicked(self):
        """CSV 내보내기 버튼 클릭 이벤트 처리"""
        try:
            # 검색 결과 확인
            if not self.search_results:
                QMessageBox.warning(self, "내보내기 실패", "내보낼 검색 결과가 없습니다.")
                return

            # 파일 저장 대화상자 표시
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV 파일 저장",
                os.path.expanduser("~/Documents/부동산_크롤링.csv"),
                "CSV 파일 (*.csv)"
            )

            if not file_path:
                return

            # 버튼 비활성화
            self.export_button.setEnabled(False)

            # 진행 상황 업데이트
            self.status_bar.showMessage("CSV 파일 저장 중...")
            self.progress_bar.setValue(50)

            # CSV 파일 저장
            saved_path = self.data_exporter.export_to_csv(
                self.search_results,
                os.path.basename(file_path),
                os.path.dirname(file_path)
            )

            if saved_path:
                # 성공 메시지 표시
                QMessageBox.information(
                    self,
                    "저장 완료",
                    f"CSV 파일이 저장되었습니다:\n{saved_path}"
                )

                # 진행 상황 업데이트
                self.status_bar.showMessage(f"CSV 파일 저장 완료: {saved_path}")
                self.progress_bar.setValue(100)
            else:
                # 오류 메시지 표시
                QMessageBox.critical(
                    self,
                    "저장 실패",
                    "CSV 파일 저장에 실패했습니다."
                )

                # 진행 상황 업데이트
                self.status_bar.showMessage("CSV 파일 저장 실패")
                self.progress_bar.setValue(0)

            # 버튼 활성화
            self.export_button.setEnabled(True)

        except Exception as e:
            logger.error(f"CSV 파일 저장 실패: {str(e)}")

            # 오류 메시지 표시
            QMessageBox.critical(
                self,
                "저장 실패",
                f"CSV 파일 저장 중 오류가 발생했습니다: {str(e)}"
            )

            # 진행 상황 업데이트
            self.status_bar.showMessage("CSV 파일 저장 실패")
            self.progress_bar.setValue(0)

            # 버튼 활성화
            self.export_button.setEnabled(True)

    def _update_page_progress(self, current_page: int, total_pages: int, result_count: int):
        """
        페이지 처리 진행 상황 업데이트

        Args:
            current_page (int): 현재 페이지 번호
            total_pages (int): 전체 페이지 수
            result_count (int): 현재까지 수집된 결과 수
        """
        try:
            # 페이지 진행 상황 업데이트
            if current_page == 0:
                # 시작 전: 총 페이지 수만 표시
                self.page_progress_label.setText(f"총 페이지 수: {total_pages}페이지")
                self.status_label.setText("검색 준비 중...")
            else:
                # 진행 중: 현재 페이지/전체 페이지 표시
                self.page_progress_label.setText(f"페이지: {current_page}/{total_pages}")
                self.status_label.setText(f"페이지 {current_page}/{total_pages} 처리 중...")

            # 진행 바 업데이트
            if total_pages > 0:
                progress = int((current_page / total_pages) * 100)
                self.progress_bar.setValue(progress)

            # 결과 수 업데이트
            self.result_count_label.setText(f"검색 결과: {result_count}개")

            # UI 업데이트
            QApplication.processEvents()

        except Exception as e:
            logger.error(f"진행 상황 업데이트 중 오류 발생: {str(e)}")

    def eventFilter(self, obj, event):
        """
        이벤트 필터

        Args:
            obj (QObject): 이벤트 발생 객체
            event (QEvent): 이벤트 객체

        Returns:
            bool: 이벤트 처리 여부
        """
        if obj is self and event.type() == CheckSearchResultsEvent.EVENT_TYPE:
            self._check_search_results()
            return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """
        창 닫기 이벤트 처리

        Args:
            event: 이벤트 객체
        """
        # 진행 중인 작업이 있는지 확인
        if hasattr(self, 'search_worker') and self.search_worker.is_alive():
            # 확인 대화상자 표시
            reply = QMessageBox.question(
                self,
                "종료 확인",
                "검색 작업이 진행 중입니다. 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 워커 스레드 종료
                self.search_worker.stop()
                self.search_worker.join(1)
                event.accept()
            else:
                event.ignore()
        else:
            # 리소스 정리
            if hasattr(self, 'region_search'):
                self.region_search.close()

            event.accept()

# 커스텀 이벤트 클래스
class CheckSearchResultsEvent(QEvent):
    """검색 결과 확인 이벤트"""

    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self):
        """이벤트 초기화"""
        super().__init__(self.EVENT_TYPE)

# 메인 함수
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
