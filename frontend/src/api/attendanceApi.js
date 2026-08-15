import apiClient from './axios';

export const attendanceApi = {
  getSheet: async (dateStr, departmentId = null, search = '') => {
    const params = { date: dateStr };
    if (departmentId) params.department_id = departmentId;
    if (search) params.search = search;
    const res = await apiClient.get('/attendance/sheet', { params });
    return res.data;
  },
  markSingle: async (data) => {
    const res = await apiClient.post('/attendance', data);
    return res.data;
  },
  markBulk: async (attendanceDate, records) => {
    const res = await apiClient.post('/attendance/bulk', {
      attendance_date: attendanceDate,
      records: records,
    });
    return res.data;
  },
  correctAttendance: async (attendanceId, correctionData) => {
    const res = await apiClient.put(`/attendance/${attendanceId}/correct`, correctionData);
    return res.data;
  },
  getEmployeeCalendar: async (employeeId, year, month) => {
    const res = await apiClient.get(`/attendance/employee/${employeeId}/calendar`, {
      params: { year, month },
    });
    return res.data;
  },
};
