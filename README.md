# QR + GPS 기반 스마트 출석 관리 시스템

학교에서 실제 사용할 수 있는 QR 코드 스캔 + GPS 위치 기반 출석 관리 시스템입니다.

## 주요 기능

- **QR 코드 출석**: QR 스캔으로 출석 페이지 접속
- **GPS 위치 검증**: 학교 반경(1000m) 내에서만 출석 가능
- **출석 시간 관리**: 야자1, 야자2, 심야야자 시간대별 출석/지각 판정
- **중복 출석 방지**: 하루 1회 출석 제한
- **관리자 대시보드**: 실시간 출석 현황 및 통계
- **학생 관리**: CRUD, Excel 일괄 등록
- **출석 관리**: 조회, 검색, 수정, 삭제
- **Excel 다운로드**: 출석 기록보내기

## 필요 라이브러리

- Python 3.8+
- Flask 3.0
- Flask-SQLAlchemy 3.1
- pandas 2.1
- openpyxl 3.1
- qrcode 7.4
- geopy 2.4
- Pillow 10.1

## 설치 방법

```bash
# 1. 프로젝트 폴더로 이동
cd QR_Attendance_System

# 2. 가상환경 생성 (권장)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt
```

## 실행 방법

```bash
python app.py
```

브라우저에서 접속:
- **학생 출석 페이지**: http://127.0.0.1:5000/
- **관리자 로그인**: http://127.0.0.1:5000/admin

## 관리자 로그인

| 항목 | 값 |
|------|-----|
| 아이디 | `teacher` |
| 비밀번호 | `1234` |

> 최초 실행 시 관리자 계정이 자동 생성됩니다. 비밀번호는 해시 방식으로 저장됩니다.

## 프로젝트 구조

```
QR_Attendance_System/
├── app.py              # Flask 메인 애플리케이션
├── config.py           # 설정 (GPS 좌표, 출석 시간 등)
├── models.py           # SQLAlchemy 데이터 모델
├── utils.py            # 유틸리티 함수
├── requirements.txt    # Python 의존성
├── README.md
├── instance/
│   └── database/       # SQLite DB (자동 생성)
├── uploads/            # Excel 업로드 임시 폴더
├── exports/            # Excel보내기 폴더
├── static/
│   ├── css/            # 스타일시트
│   ├── js/             # JavaScript
│   ├── images/
│   └── qr/             # QR 코드 이미지 (자동 생성)
└── templates/          # Jinja2 HTML 템플릿
```

## 출석 시간 설정

| 세션 | 정시 출석 | 지각 |
|------|-----------|------|
| 야자1 | 18:30 ~ 18:40 | 18:40 ~ 20:09 |
| 야자2 | 20:10 ~ 20:20 | 20:20 ~ 21:19 |
| 심야야자 | 21:20 ~ 21:30 | 21:30 ~ 23:59 |

## GPS 설정

`config.py`에서 출석 허용 좌표와 반경을 변경할 수 있습니다:

```python
ALLOWED_LOCATIONS = [
    {'name': '본교', 'latitude': 36.9897, 'longitude': 129.4087},
    {'name': '추가 위치', 'latitude': 36.893, 'longitude': 129.377},
]
ALLOWED_RADIUS_METERS = 1000
```

등록된 위치 중 **어느 한 곳**의 반경(1000m) 안에 있으면 출석이 가능합니다.

## Excel 업로드 형식

학생 명단 Excel(.xlsx) 파일 형식:

| 학번 | 이름 | 학년 | 반 | 번호 |
|------|------|------|-----|------|
| 2024001 | 홍길동 | 1 | 3 | 15 |

## 사용 흐름

1. 관리자 로그인 후 학생 명단 등록 (개별 추가 또는 Excel 업로드)
2. 대시보드에서 QR 코드 확인/출력
3. 학생이 QR 스캔 → 학번/이름 입력 → GPS 확인 → 출석 완료
4. 관리자가 대시보드에서 출석 현황 확인 및 Excel 다운로드

## 기술 스택

- **Backend**: Python 3, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite
- **기타**: pandas, openpyxl, qrcode, geopy
