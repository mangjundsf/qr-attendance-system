/**
 * 학생 출석 페이지 JavaScript
 * GPS 기반 출석 처리
 */
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('attendanceForm');
    const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
    const confirmBtn = document.getElementById('confirmBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const errorAlert = document.getElementById('errorAlert');
    const submitBtn = document.getElementById('submitBtn');

    let pendingData = null;
    let isSubmitting = false;

    /** 오류 메시지 표시 */
    function showError(message) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    }

    /** 오류 메시지 숨기기 */
    function hideError() {
        errorAlert.classList.add('d-none');
    }

    /** 폼 제출 - 확인 팝업 표시 */
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        hideError();

        const studentId = document.getElementById('student_id').value.trim();
        const name = document.getElementById('name').value.trim();

        if (!studentId || !name) {
            showError('학번과 이름을 모두 입력해주세요.');
            return;
        }

        pendingData = { student_id: studentId, name: name };
        document.getElementById('confirmInfo').textContent =
            `학번: ${studentId} / 이름: ${name}`;
        confirmModal.show();
    });

    /** 확인 버튼 - GPS 위치 확인 후 출석 처리 */
    confirmBtn.addEventListener('click', function () {
        confirmModal.hide();
        if (!pendingData || isSubmitting) return;

        if (!navigator.geolocation) {
            showError('이 브라우저는 GPS를 지원하지 않습니다.');
            return;
        }

        isSubmitting = true;
        submitBtn.disabled = true;
        loadingOverlay.classList.remove('d-none');

        navigator.geolocation.getCurrentPosition(
            function (position) {
                submitAttendance(
                    pendingData.student_id,
                    pendingData.name,
                    position.coords.latitude,
                    position.coords.longitude
                );
            },
            function (error) {
                loadingOverlay.classList.add('d-none');
                isSubmitting = false;
                submitBtn.disabled = false;

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        showError('GPS 권한이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해주세요.');
                        break;
                    case error.POSITION_UNAVAILABLE:
                        showError('위치 정보를 사용할 수 없습니다.');
                        break;
                    case error.TIMEOUT:
                        showError('GPS 위치 확인 시간이 초과되었습니다. 다시 시도해주세요.');
                        break;
                    default:
                        showError('GPS 오류가 발생했습니다.');
                }
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    });

    /** 출석 API 호출 */
    async function submitAttendance(studentId, name, latitude, longitude) {
        try {
            const response = await fetch('/api/check-attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: studentId,
                    name: name,
                    latitude: latitude,
                    longitude: longitude,
                }),
            });

            const data = await response.json();

            if (data.success) {
                // PRG 패턴: 리다이렉트로 중복 저장 방지
                window.location.replace(data.redirect);
            } else {
                showError(data.message);
            }
        } catch (err) {
            showError('서버 연결에 실패했습니다. 다시 시도해주세요.');
        } finally {
            loadingOverlay.classList.add('d-none');
            isSubmitting = false;
            submitBtn.disabled = false;
        }
    }
});
