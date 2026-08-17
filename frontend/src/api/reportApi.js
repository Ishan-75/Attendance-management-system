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
  // Direct client-side file downloader with JWT authentication and fallback error handling
  downloadReport: async (format, params) => {
    const endpoints = {
      excel: '/reports/export-excel',
      csv: '/reports/export-csv',
      json: '/reports/export-json',
      html: '/reports/export-html',
    };
    const endpoint = endpoints[format] || endpoints.excel;

    try {
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

      const rawData = format === 'json' ? JSON.stringify(res.data, null, 2) : res.data;
      const blob = new Blob([rawData], {
        type: mimeTypes[format] || 'application/octet-stream',
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const start = params.start_date || 'report';
      const end = params.end_date || 'report';
      link.download = `attendance_statement_${start}_to_${end}.${extensions[format] || 'dat'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        const errText = await err.response.data.text();
        try {
          const errJson = JSON.parse(errText);
          throw new Error(errJson.detail || errJson.message || 'Export generation failed');
        } catch (e) {
          throw new Error(errText || 'Export generation failed');
        }
      }
      throw err;
    }
  },
};
