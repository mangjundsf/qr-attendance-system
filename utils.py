"""출석 관련 유틸리티 함수"""
from datetime import datetime, time
from zoneinfo import Zoneinfo

from geopy.distance import geodesic

import config


def calculate_distance(lat1, lon1, lat2, lon2):
    """두 GPS 좌표 간 거리를 미터 단위로 계산"""
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def is_within_radius(latitude, longitude):
    """허용된 출석 위치 중 하나의 반경 내에 있는지 확인"""
    min_distance = float('inf')
    nearest_location = None

    for location in config.ALLOWED_LOCATIONS:
        distance = calculate_distance(
            latitude, longitude,
            location['latitude'], location['longitude']
        )
        if distance < min_distance:
            min_distance = distance
            nearest_location = location['name']

    within = min_distance <= config.ALLOWED_RADIUS_METERS
    return within, min_distance, nearest_location


def get_current_slot(now=None):
    """
    현재 시간에 해당하는 출석 시간대와 상태를 반환
    Returns: (session_name, status, error_message)
    """
    if now is None:
        now = datetime.now(ZoneInfo("Asia/Seoul"))

    current_time = now.time()
    first_slot = config.ATTENDANCE_SLOTS[0]
    first_start = time(first_slot['start_hour'], first_slot['start_minute'])

    if current_time < first_start:
        return None, None, '아직 출석 시간이 아닙니다.'

    for slot in config.ATTENDANCE_SLOTS:
        start = time(slot['start_hour'], slot['start_minute'])
        end = time(slot['end_hour'], slot['end_minute'])
        late_until = time(slot['late_until_hour'], slot['late_until_minute'])

        if start <= current_time <= end:
            return slot['name'], '출석', None

        if end < current_time <= late_until:
            return slot['name'], '지각', None

    last_slot = config.ATTENDANCE_SLOTS[-1]
    last_end = time(last_slot['end_hour'], last_slot['end_minute'])
    if current_time > last_end:
        return last_slot['name'], '지각', None

    return None, None, '출석 가능한 시간이 아닙니다.'


def get_today_stats():
    """오늘 출석 통계 계산"""
    from models import Attendance, Student, db

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    total_students = Student.query.count()
    today_records = Attendance.query.filter_by(date=today).all()

    present = sum(1 for r in today_records if r.status == '출석')
    late = sum(1 for r in today_records if r.status == '지각')
    attended = present + late
    absent = max(0, total_students - attended)

    rate = round((attended / total_students * 100), 1) if total_students > 0 else 0

    return {
        'total': total_students,
        'present': present,
        'late': late,
        'absent': absent,
        'attended_today': attended,
        'rate': rate,
    }


def get_student_attendance_rates(student_id):
    """학생별 출석률, 지각률, 결석률 계산"""
    from models import Attendance, db
    from sqlalchemy import func

    records = Attendance.query.filter_by(student_id=student_id).all()
    total_days = len(records)

    if total_days == 0:
        return {'present_rate': 0, 'late_rate': 0, 'absent_rate': 0, 'total_days': 0}

    present = sum(1 for r in records if r.status == '출석')
    late = sum(1 for r in records if r.status == '지각')

    return {
        'present_rate': round(present / total_days * 100, 1),
        'late_rate': round(late / total_days * 100, 1),
        'absent_rate': 0,
        'total_days': total_days,
    }


def get_attendance_statistics():
    """전체 출석 통계 (관리자 대시보드용)"""
    from models import Attendance, Student, db
    from sqlalchemy import func

    total_students = Student.query.count()
    total_records = Attendance.query.count()

    if total_records == 0:
        return {
            'total_records': 0,
            'present_count': 0,
            'late_count': 0,
            'present_rate': 0,
            'late_rate': 0,
            'by_grade': [],
            'by_session': [],
        }

    present_count = Attendance.query.filter_by(status='출석').count()
    late_count = Attendance.query.filter_by(status='지각').count()

    by_grade = db.session.query(
        Student.grade,
        func.count(Attendance.id).label('count')
    ).join(
        Attendance, Student.student_id == Attendance.student_id
    ).group_by(Student.grade).all()

    by_session = db.session.query(
        Attendance.session,
        func.count(Attendance.id).label('count')
    ).group_by(Attendance.session).all()

    return {
        'total_records': total_records,
        'present_count': present_count,
        'late_count': late_count,
        'present_rate': round(present_count / total_records * 100, 1),
        'late_rate': round(late_count / total_records * 100, 1),
        'by_grade': [{'grade': g, 'count': c} for g, c in by_grade],
        'by_session': [{'session': s or '미지정', 'count': c} for s, c in by_session],
    }
