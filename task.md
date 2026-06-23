# 📋 소방 관제 프로젝트 Task & Progress Tracker

본 체크리스트는 **6명의 팀원(Python 2개월차, HTML/CSS/JS 1달 미만)**이 각 파트별로 4주 동안 독립적으로 수행해야 할 작업 항목들과 진척 상황을 추적하기 위해 작성되었습니다.

---

## 🚦 전체 프로젝트 상태 및 로드맵
- **프로젝트 기간**: 4주 (현재 1주차 진행 중)
- **목표**: 드론 및 ESP32-Cam RGB 스트리밍 기반 실시간 불/연기 탐지 데모 완성

---

## 👥 파트별 상세 TODO 및 담당 파일

### 1. 🤖 AI & 영상 처리 (1명)
> **목표**: 불/연기 이미지 학습 및 실시간 OpenCV 프레임 디텍션 구현
- [ ] Roboflow Universe에서 적합한 "Fire and Smoke" 데이터셋(2,000~5,000장 수준) 찾기
- [ ] Google Colab을 활용하여 YOLOv8m 모델 학습시키기 (epochs=50 추천)
- [ ] 학습된 최적 가중치 파일 `best.pt`를 다운로드하여 `ai/` 폴더에 배치
- [ ] [camera_manager.py](file:///c:/kdm/1stProject/ai/camera_manager.py) 파일 수정
  - `model = YOLO("ai/best.pt")` 연동 적용
  - 본인 학습 모델의 클래스 번호(예: 0=FIRE, 1=SMOKE)에 맞춰 `class_id` 매핑 수정

### 2. 🔌 PM & 하드웨어 제어 (1명)
> **목표**: 드론 및 ESP32-Cam 전원/네트워크 구성 및 영상 스트림 활성화
- [ ] ESP32-Cam 모듈 조립 및 Wi-Fi 연결 아두이노 코드 업로드
- [ ] ESP32-Cam 영상 스트리밍 활성화 및 IP 주소 획득
- [ ] [camera_manager.py](file:///c:/kdm/1stProject/ai/camera_manager.py)의 `ESP32_STREAM_URL` 값을 획득한 IP 주소로 수정 및 통신 연결 테스트
- [ ] 파이드론 기본 비행 스크립트 작성 및 시연 비행 연습
- [ ] 발표 PPT 구성 및 템플릿 제작 총괄

### 3. ⚙️ 웹 백엔드 A (1명)
> **목표**: Flask 서버 인프라 및 DB(JSON) 기록 관리 기능 구현
- [ ] [json_manager.py](file:///c:/kdm/1stProject/utils/json_manager.py)를 기반으로 회원 정보 및 화재 발생 기록 구조 안정성 검토
- [ ] 화재 감지 시 [fire_logs.json](file:///c:/kdm/1stProject/db/fire_logs.json)에 기록이 시간순으로 누적되는지 CRUD 테스트
- [ ] 로그인, 회원가입, 회원정보 수정 청사진(Blueprint) 로직 기능 점검 ([auth/routes.py](file:///c:/kdm/1stProject/blueprints/auth/routes.py))

### 4. ⚙️ 웹 백엔드 B (1명)
> **목표**: 영상 스트리밍 라우팅 및 실시간 API 데이터 연동, SNS 알림 기능 구현
- [ ] [dashboard/routes.py](file:///c:/kdm/1stProject/blueprints/dashboard/routes.py)의 비디오 피드 스트리밍 FPS 조절 및 끊김 방지 최적화
- [ ] 텔레그램 봇 토큰 발급 및 `requests` 모듈 활용 파이썬 알림 전송 기능 작성
- [ ] 화재 감지 트리거가 켜질 때 텔레그램 방으로 **"경보! 불 감지!"** 메시지와 사진 전송 로직 탑재
- [ ] `/dashboard/api/logs` 및 `/dashboard/api/latest_alert` API 엔드포인트 세부 기능 개발

### 5. 🎨 웹 프론트엔드 A (1명)
> **목표**: 대시보드 실시간 모니터링 화면(UI) 및 실시간 알림음(JS) 구현
- [ ] [monitor.html](file:///c:/kdm/1stProject/templates/dashboard/monitor.html)을 기반으로 소방 관제 테마에 맞는 메인 레이아웃 및 CSS 고도화
- [ ] [dashboard.js](file:///c:/kdm/1stProject/static/js/dashboard.js) 수정
  - 2초 간격 숏 폴링을 통한 실시간 화재 로그 테이블 추가 동기화 처리
  - `/api/latest_alert`의 위험 신호 감지 시, `emergency-overlay` 붉은 점멸 애니메이션 가동
  - 사용자 인터랙션 후 사이렌 소리(siren.mp3) 자동 재생 및 음소거 해제 버튼 작동 보장

### 6. 🎨 웹 프론트엔드 B (1명)
> **목표**: 감지 이력 조회 페이지 및 Chart.js 통계 그래프, Leaflet.js 지도 마킹 구현
- [ ] [history.html](file:///c:/kdm/1stProject/templates/dashboard/history.html) 레이아웃 마크업 작업 및 Bootstrap 스타일 고도화
- [ ] [history.js](file:///c:/kdm/1stProject/static/js/history.js) 수정
  - Chart.js 연동하여 누적 감지 건수 도넛형 차트 시각화 완성
  - Leaflet.js 지도에 드론 및 기기 좌표를 수동/자동 마커로 맵핑 표시
  - 전체 로그 이력을 최신 시간순 테이블 형태로 목록 출력 기능 안정화
