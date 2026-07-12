"""QR + GPS 기반 스마트 출석 관리 시스템"""
import os
from datetime import datetime
from zoneinfo import Zoneinfo
from functools import wraps
from io import BytesIO

import pandas as pd
import qrcode
from flask import (
    Flask, flash, jsonify, redirect, render_template,
    request, send_file, session, url_for,
)
from werkzeug.utils import secure_filename

import config
from models import Admin, Attendance, Student, db
from utils import (
    get_attendance_statistics,
    get_current_slot,
    get_student_attendance_rates,
    get_today_stats,
    is_within_radius,
)

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)


def login_required(f):
    """관리자 로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('관리자 로그인이 필요합니다.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def init_database():
    """데이터베이스 및 기본 데이터 초기화"""
    os.makedirs(os.path.join(config.BASE_DIR, 'instance', 'database'), exist_ok=True)
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.EXPORT_FOLDER, exist_ok=True)
    os.makedirs(config.QR_FOLDER, exist_ok=True)

    with app.app_context():
        db.create_all()

        if not Admin.query.filter_by(username=config.DEFAULT_ADMIN_USERNAME).first():
            admin = Admin(username=config.DEFAULT_ADMIN_USERNAME)
            admin.set_password(config.DEFAULT_ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()

        generate_qr_code()


def generate_qr_code():
    """출석 페이지 QR 코드 자동 생성"""
    qr_path = os.path.join(config.QR_FOLDER, 'attendance_qr.png')
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data('https://qr-attendance-system-nmj6.onrender.com')
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0d6efd', back_color='white')
    img.save(qr_path)


# ==================== 학생 출석 페이지 ====================

@app.route('/')
def index():
    """학생 출석 메인 페이지"""
    stats = get_today_stats()
    return render_template('index.html', stats=stats)


@app.route('/api/check-attendance', methods=['POST'])
def check_attendance():
    """출석 처리 API"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'}), 400

    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not student_id or not name:
        return jsonify({'success': False, 'message': '학번과 이름을 모두 입력해주세요.'}), 400

    if latitude is None or longitude is None:
        return jsonify({'success': False, 'message': 'GPS 위치 정보를 가져올 수 없습니다.'}), 400

    student = Student.query.filter_by(student_id=student_id, name=name).first()
    if not student:
        return jsonify({'success': False, 'message': '등록되지 않은 학생입니다. 학번과 이름을 확인해주세요.'}), 404

    today = datetime.now().date()
    existing = Attendance.query.filter_by(student_id=student_id, date=today).first()
    if existing:
        return jsonify({'success': False, 'message': '이미 오늘 출석하였습니다.'}), 409

    within_radius, distance, nearest_location = is_within_radius(latitude, longitude)
    if not within_radius:
        return jsonify({
            'success': False,
            'message': f'출석 가능한 위치가 아닙니다. (가장 가까운 출석지로부터 {distance:.0f}m)',
        }), 403

    session_name, status, error = get_current_slot()
    if error:
        return jsonify({'success': False, 'message': error}), 400

    now = datetime.now()
    attendance = Attendance(
        student_id=student.student_id,
        student_name=student.name,
        date=today,
        time=now.time(),
        status=status,
        session=session_name,
        latitude=latitude,
        longitude=longitude,
        distance=round(distance, 2),
    )
    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'success': True,
        'redirect': url_for('success', id=attendance.id),
    })


@app.route('/success/<int:id>')
def success(id):
    """출석 완료 페이지"""
    record = Attendance.query.get_or_404(id)
    return render_template('success.html', record=record)


# ==================== 관리자 인증 ====================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인"""
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('아이디와 비밀번호를 입력해주세요.', 'danger')
            return render_template('admin_login.html')

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('로그인 성공!', 'success')
            return redirect(url_for('dashboard'))

        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('admin_login'))


# ==================== 관리자 대시보드 ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """관리자 메인 대시보드"""
    stats = get_today_stats()
    attendance_stats = get_attendance_statistics()
    today = datetime.now().strftime('%Y년 %m월 %d일')

    recent = Attendance.query.order_by(Attendance.created_at.desc()).limit(10).all()

    return render_template(
        'dashboard.html',
        stats=stats,
        attendance_stats=attendance_stats,
        today=today,
        recent=recent,
    )


# ==================== 학생 관리 ====================

@app.route('/students')
@login_required
def students():
    """학생 목록 조회"""
    search = request.args.get('search', '').strip()
    grade = request.args.get('grade', '')
    class_number = request.args.get('class_number', '')

    query = Student.query

    if search:
        query = query.filter(
            db.or_(
                Student.student_id.contains(search),
                Student.name.contains(search),
            )
        )
    if grade:
        query = query.filter_by(grade=int(grade))
    if class_number:
        query = query.filter_by(class_number=int(class_number))

    students_list = query.order_by(
        Student.grade, Student.class_number, Student.student_number
    ).all()

    for s in students_list:
        s.rates = get_student_attendance_rates(s.student_id)

    return render_template(
        'students.html',
        students=students_list,
        search=search,
        grade=grade,
        class_number=class_number,
    )


@app.route('/api/students', methods=['POST'])
@login_required
def add_student():
    """학생 추가"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    name = data.get('name', '').strip()
    grade = data.get('grade')
    class_number = data.get('class_number')
    student_number = data.get('student_number')

    if not all([student_id, name, grade, class_number, student_number]):
        return jsonify({'success': False, 'message': '모든 항목을 입력해주세요.'}), 400

    if Student.query.filter_by(student_id=student_id).first():
        return jsonify({'success': False, 'message': '이미 등록된 학번입니다.'}), 409

    student = Student(
        student_id=student_id,
        name=name,
        grade=int(grade),
        class_number=int(class_number),
        student_number=int(student_number),
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({'success': True, 'message': '학생이 등록되었습니다.'})


@app.route('/api/students/<int:id>', methods=['PUT'])
@login_required
def update_student(id):
    """학생 정보 수정"""
    student = Student.query.get_or_404(id)
    data = request.get_json()

    new_student_id = data.get('student_id', '').strip()
    if new_student_id != student.student_id:
        if Student.query.filter_by(student_id=new_student_id).first():
            return jsonify({'success': False, 'message': '이미 등록된 학번입니다.'}), 409
        student.student_id = new_student_id

    student.name = data.get('name', student.name).strip()
    student.grade = int(data.get('grade', student.grade))
    student.class_number = int(data.get('class_number', student.class_number))
    student.student_number = int(data.get('student_number', student.student_number))

    db.session.commit()
    return jsonify({'success': True, 'message': '학생 정보가 수정되었습니다.'})


@app.route('/api/students/<int:id>', methods=['DELETE'])
@login_required
def delete_student(id):
    """학생 삭제"""
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True, 'message': '학생이 삭제되었습니다.'})


# ==================== 출석 관리 ====================

@app.route('/attendance')
@login_required
def attendance_list():
    """출석 목록 조회"""
    search = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '')
    grade = request.args.get('grade', '')
    class_number = request.args.get('class_number', '')

    query = Attendance.query

    if search:
        query = query.filter(
            db.or_(
                Attendance.student_id.contains(search),
                Attendance.student_name.contains(search),
            )
        )
    if date_filter:
        query = query.filter_by(date=datetime.strptime(date_filter, '%Y-%m-%d').date())
    if grade or class_number:
        student_query = Student.query
        if grade:
            student_query = student_query.filter_by(grade=int(grade))
        if class_number:
            student_query = student_query.filter_by(class_number=int(class_number))
        student_ids = [s.student_id for s in student_query.all()]
        query = query.filter(Attendance.student_id.in_(student_ids))

    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()

    return render_template(
        'attendance.html',
        records=records,
        search=search,
        date_filter=date_filter,
        grade=grade,
        class_number=class_number,
    )


@app.route('/api/attendance/<int:id>', methods=['PUT'])
@login_required
def update_attendance(id):
    """출석 기록 수정"""
    record = Attendance.query.get_or_404(id)
    data = request.get_json()

    if 'status' in data:
        record.status = data['status']
    if 'session' in data:
        record.session = data['session']
    if 'time' in data and data['time']:
        record.time = datetime.strptime(data['time'], '%H:%M').time()

    db.session.commit()
    return jsonify({'success': True, 'message': '출석 기록이 수정되었습니다.'})


@app.route('/api/attendance/<int:id>', methods=['DELETE'])
@login_required
def delete_attendance(id):
    """출석 기록 삭제"""
    record = Attendance.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '출석 기록이 삭제되었습니다.'})


# ==================== Excel 업로드/다운로드 ====================

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """학생 명단 Excel 업로드"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('파일을 선택해주세요.', 'danger')
            return redirect(url_for('upload'))

        file = request.files['file']
        if file.filename == '':
            flash('파일을 선택해주세요.', 'danger')
            return redirect(url_for('upload'))

        if not allowed_file(file.filename):
            flash('Excel 파일(.xlsx)만 업로드 가능합니다.', 'danger')
            return redirect(url_for('upload'))

        try:
            df = pd.read_excel(file)
            required_cols = ['학번', '이름', '학년', '반', '번호']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                flash(f'필수 열이 없습니다: {", ".join(missing)}', 'danger')
                return redirect(url_for('upload'))

            success_count = 0
            duplicate_count = 0

            for _, row in df.iterrows():
                student_id = str(row['학번']).strip()
                if Student.query.filter_by(student_id=student_id).first():
                    duplicate_count += 1
                    continue

                student = Student(
                    student_id=student_id,
                    name=str(row['이름']).strip(),
                    grade=int(row['학년']),
                    class_number=int(row['반']),
                    student_number=int(row['번호']),
                )
                db.session.add(student)
                success_count += 1

            db.session.commit()
            flash(
                f'등록 완료: {success_count}명 성공, {duplicate_count}명 중복 건너뜀',
                'success',
            )
        except Exception as e:
            flash(f'Excel 파일 처리 중 오류: {str(e)}', 'danger')

        return redirect(url_for('upload'))

    return render_template('upload.html')


@app.route('/export/today')
@login_required
def export_today():
    """오늘 출석 기록 Excel 다운로드"""
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    records = Attendance.query.filter_by(date=today).order_by(Attendance.time).all()

    data = []
    for r in records:
        student = Student.query.filter_by(student_id=r.student_id).first()
        data.append({
            '학번': r.student_id,
            '이름': r.student_name,
            '학년': student.grade if student else '',
            '반': student.class_number if student else '',
            '번호': student.student_number if student else '',
            '날짜': r.date.strftime('%Y-%m-%d'),
            '출석시간': r.time.strftime('%H:%M:%S'),
            '상태': r.status,
            '세션': r.session,
            '위도': r.latitude,
            '경도': r.longitude,
            '거리(m)': r.distance,
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='출석기록')
    output.seek(0)

    filename = f'attendance_{today.strftime("%Y_%m_%d")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename,
    )


@app.route('/export/attendance')
@login_required
def export_attendance():
    """필터된 출석 기록 Excel 다운로드"""
    search = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '')

    query = Attendance.query
    if search:
        query = query.filter(
            db.or_(
                Attendance.student_id.contains(search),
                Attendance.student_name.contains(search),
            )
        )
    if date_filter:
        query = query.filter_by(date=datetime.strptime(date_filter, '%Y-%m-%d').date())

    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()

    data = [{
        '학번': r.student_id,
        '이름': r.student_name,
        '날짜': r.date.strftime('%Y-%m-%d'),
        '출석시간': r.time.strftime('%H:%M:%S'),
        '상태': r.status,
        '세션': r.session,
        '위도': r.latitude,
        '경도': r.longitude,
        '거리(m)': r.distance,
    } for r in records]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='출석기록')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='attendance_export.xlsx',
    )


if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
