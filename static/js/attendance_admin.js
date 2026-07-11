/** 출석 관리 JavaScript */
document.addEventListener('DOMContentLoaded', function () {
    const editModal = new bootstrap.Modal(document.getElementById('editAttendanceModal'));

    /** 출석 수정 모달 열기 */
    document.querySelectorAll('.edit-att-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('editAttId').value = btn.dataset.id;
            document.getElementById('editAttStatus').value = btn.dataset.status;
            document.getElementById('editAttSession').value = btn.dataset.session || '야자1';
            document.getElementById('editAttTime').value = btn.dataset.time;
            editModal.show();
        });
    });

    /** 출석 기록 수정 */
    document.getElementById('updateAttBtn').addEventListener('click', async function () {
        const id = document.getElementById('editAttId').value;
        const data = {
            status: document.getElementById('editAttStatus').value,
            session: document.getElementById('editAttSession').value,
            time: document.getElementById('editAttTime').value,
        };

        const result = await apiRequest(`/api/attendance/${id}`, 'PUT', data);
        if (result.success) {
            showAlert(result.message, 'success');
            editModal.hide();
            setTimeout(() => location.reload(), 500);
        } else {
            showAlert(result.message, 'danger');
        }
    });

    /** 출석 기록 삭제 */
    document.querySelectorAll('.delete-att-btn').forEach(function (btn) {
        btn.addEventListener('click', async function () {
            if (!confirm(`"${btn.dataset.name}" 학생의 출석 기록을 삭제하시겠습니까?`)) return;

            const result = await apiRequest(`/api/attendance/${btn.dataset.id}`, 'DELETE');
            if (result.success) {
                showAlert(result.message, 'success');
                setTimeout(() => location.reload(), 500);
            } else {
                showAlert(result.message, 'danger');
            }
        });
    });
});
