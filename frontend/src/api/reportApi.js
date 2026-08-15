import apiClient from './axios';

const getBaseUrl = () => import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const reportApi = {
  getAttendanceReport: async (params) => {
    const res = await apiClient.get('/reports/attendance', { params });
    return res.data;
  },
  getExportCsvUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${getBaseUrl()}/reports/export-csv?${query}`;
  },
  getExportExcelUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${getBaseUrl()}/reports/export-excel?${query}`;
  },
  getExportJsonUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${getBaseUrl()}/reports/export-json?${query}`;
  },
  getExportHtmlUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${getBaseUrl()}/reports/export-html?${query}`;
  },
  // Direct client-side file downloader with JWT token attached
  downloadReport: async (format, params) => {
    const endpoints = {
      excel: '/reports/export-excel',
      csv: '/reports/export-csv',
      json: '/reports/export-json',
      html: '/reports/export-html',
    };
    const endpoint = endpoints[format] || endpoints.excel;
    const res = await apiClient.get(endpoint, {
      params,
      responseType: format === 'json' ? 'json' : 'blob',
    });

    if (format === 'html') {
      const blob = new Blob([res.data], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      return;
    }

    const extensions = {
      excel: 'xlsx',
      csv: 'csv',
      json: 'json',
    };
    const mimeTypes = {
      excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      csv: 'text/csv',
      json: 'application/json',
    };

    const blob = new Blob([format === 'json' ? JSON.stringify(res.data, null, 2) : res.data], {
      type: mimeTypes[format] || 'application/octet-stream',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `attendance_report_${params.start_date}_to_${params.end_date}.${extensions[format] || 'dat'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
