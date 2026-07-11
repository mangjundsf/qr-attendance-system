/** 학생 관리 JavaScript */
document.addEventListener('DOMContentLoaded', function () {
    const addModal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    const editModal = new bootstrap.Modal(document.getElementById('editStudentModal'));

    /** 학생 추가 */
    document.getElementById('saveStudentBtn').addEventListener('click', async function () {
        const form = document.getElementById('addStudentForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const result = await apiRequest('/api/students', 'POST', data);
        if (result.success) {
            showAlert(result.message, 'success');
            addModal.hide();
            setTimeout(() => location.reload(), 500);
        } else {
            showAlert(result.message, 'danger');
        }
    });

    /** 학생 수정 모달 열기 */
    document.querySelectorAll('.edit-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('editId').value = btn.dataset.id;
            document.getElementById('editStudentId').value = btn.dataset.studentId;
            document.getElementById('editName').value = btn.dataset.name;
            document.getElementById('editGrade').value = btn.dataset.grade;
            document.getElementById('editClass').value = btn.dataset.class;
            document.getElementById('editNumber').value = btn.dataset.number;
            editModal.show();
        });
    });

    /** 학생 수정 저장 */
    document.getElementById('updateStudentBtn').addEventListener('click', async function () {
        const id = document.getElementById('editId').value;
        const data = {
            student_id: document.getElementById('editStudentId').value,
            name: document.getElementById('editName').value,
            grade: document.getElementById('editGrade').value,
            class_number: document.getElementById('editClass').value,
            student_number: document.getElementById('editNumber').value,
        };

        const result = await apiRequest(`/api/students/${id}`, 'PUT', data);
        if (result.success) {
            showAlert(result.message, 'success');
            editModal.hide();
            setTimeout(() => location.reload(), 500);
        } else {
            showAlert(result.message, 'danger');
        }
    });

    /** 학생 삭제 */
    document.querySelectorAll('.delete-btn').forEach(function (btn) {
        btn.addEventListener('click', async function () {
            if (!confirm(`"${btn.dataset.name}" 학생을 삭제하시겠습니까?`)) return;

            const result = await apiRequest(`/api/students/${btn.dataset.id}`, 'DELETE');
            if (result.success) {
                showAlert(result.message, 'success');
                setTimeout(() => location.reload(), 500);
            } else {
                showAlert(result.message, 'danger');
            }
        });
    });
});
