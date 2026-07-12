"""애플리케이션 설정"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask 설정
SECRET_KEY = os.environ.get('SECRET_KEY', 'qr-attendance-secret-key-2024')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
    BASE_DIR, 'instance', 'database', 'attendance.db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 출석 허용 GPS 좌표 (반경 내 어느 위치든 출석 가능)
ALLOWED_LOCATIONS = [
    {
        'name': '본교',
        'latitude': 36.9897,
        'longitude': 129.4087,
    },
]
ALLOWED_RADIUS_METERS = 100000000000

# 하위 호환용 (첫 번째 위치)
SCHOOL_LATITUDE = ALLOWED_LOCATIONS[0]['latitude']
SCHOOL_LONGITUDE = ALLOWED_LOCATIONS[0]['longitude']

# 출석 시간대 설정
ATTENDANCE_SLOTS = [
     {
        'name': '확인용',
        'start_hour': 0,        # 00 대신 0으로 수정 (문법 에러 방지)
        'start_minute': 10,
        'end_hour': 22,         # 23 대신 22로 수정 (지각 버퍼가 더해져도 23시가 되도록 안전하게 설정)
        'end_minute': 0,        # 00 대신 0으로 수정 (문법 에러 방지)
    },
]


# 파일 업로드 설정
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
ALLOWED_EXTENSIONS = {'xlsx'}

# 기본 관리자 계정
DEFAULT_ADMIN_USERNAME = 'teacher'
DEFAULT_ADMIN_PASSWORD = '1234'
