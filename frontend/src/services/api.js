// f:\CN Hackathon\frontend\src\services\api.js

const API_BASE = '/api';

function getAuthHeaders() {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };

  // If body is not FormData, default to JSON
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (networkError) {
    // Network-level failure: backend is unreachable, DNS failure, CORS, etc.
    throw new Error('Could not connect to the server. Please check your connection and try again.');
  }

  if (!response.ok) {
    let errorMsg = `Request failed (${response.status})`;
    try {
      const errJson = await response.json();
      errorMsg = errJson.detail || errJson.message || errorMsg;
    } catch (e) {
      // Failed to parse JSON error
    }

    // Surface authentication errors with a clear message
    if (response.status === 401 || response.status === 403) {
      throw new Error(errorMsg === `Request failed (${response.status})` ? 'Not authenticated. Please log in again.' : errorMsg);
    }

    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  // Authentication
  login: async (email, password) => {
    const data = await request('/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
    }
    return data;
  },

  register: async (name, email, password) => {
    const data = await request('/auth/register', {
      method: 'POST',
      body: { name, email, password },
    });
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
    }
    return data;
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  },

  getMe: async () => {
    return request('/auth/me');
  },

  // Dashboard & Analytics
  getImpactStats: async () => {
    return request('/dashboard/impact');
  },

  getHotspots: async (category = '', days = 90) => {
    let url = `/dashboard/hotspots?days=${days}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    return request(url);
  },

  // Issues
  listIssues: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.status) params.append('status', filters.status);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.bbox) params.append('bbox', filters.bbox);
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/issues${query}`);
  },

  getIssue: async (id) => {
    return request(`/issues/${id}`);
  },

  createIssue: async (formData) => {
    // formData should be an instance of FormData (contains title, description, latitude, longitude, category_hint, images, video)
    return request('/issues', {
      method: 'POST',
      body: formData,
    });
  },

  verifyIssue: async (id, type) => {
    return request(`/issues/${id}/verify`, {
      method: 'POST',
      body: { type },
    });
  },

  // Comments
  getComments: async (id, page = 1, limit = 20) => {
    return request(`/issues/${id}/comments?page=${page}&limit=${limit}`);
  },

  createComment: async (id, content) => {
    return request(`/issues/${id}/comments`, {
      method: 'POST',
      body: { content },
    });
  },

  // Gamification
  getLeaderboard: async (limit = 50, stateId = null) => {
    let url = `/leaderboard?limit=${limit}`;
    if (stateId) {
      url += `&state_id=${stateId}`;
    }
    return request(url);
  },

  getStates: async () => {
    return request('/states');
  },

  updateMyState: async (stateId) => {
    return request('/auth/me/state', {
      method: 'PATCH',
      body: { state_id: stateId }
    });
  },

  getUserBadges: async (userId) => {
    return request(`/users/${userId}/badges`);
  },

  // Notifications
  listNotifications: async (page = 1, limit = 20) => {
    return request(`/notifications?page=${page}&limit=${limit}`);
  },

  markNotificationAsRead: async (id) => {
    return request(`/notifications/${id}/read`, {
      method: 'PATCH',
    });
  },

  // Admin Operations
  adminListIssues: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.status) params.append('status', filters.status);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.assigned_department_id) params.append('assigned_department_id', filters.assigned_department_id);
    if (filters.assigned_to_user_id) params.append('assigned_to_user_id', filters.assigned_to_user_id);
    if (filters.is_unassigned !== undefined) params.append('is_unassigned', filters.is_unassigned);
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/admin/issues${query}`);
  },

  assignIssue: async (id, departmentId, userId) => {
    return request(`/admin/issues/${id}/assign`, {
      method: 'PATCH',
      body: {
        assigned_department_id: departmentId || null,
        assigned_to_user_id: userId || null,
      },
    });
  },

  adminUpdateIssue: async (id, updates = {}) => {
    return request(`/admin/issues/${id}`, {
      method: 'PATCH',
      body: updates,
    });
  },

  adminListUsers: async () => {
    return request('/admin/users');
  },

  adminUpdateUserRole: async (userId, role) => {
    return request(`/admin/users/${userId}/role`, {
      method: 'PATCH',
      body: { role },
    });
  },

  getDepartments: async () => {
    return request('/departments');
  },

  createDepartment: async (name, categories, regionId = null) => {
    return request('/admin/departments', {
      method: 'POST',
      body: { name, category_mapping: categories, region_id: regionId },
    });
  },

  getDepartmentPerformance: async () => {
    return request('/dashboard/departments');
  },

  followIssue: async (id) => {
    return request(`/issues/${id}/follow`, {
      method: 'POST',
    });
  },

  unfollowIssue: async (id) => {
    return request(`/issues/${id}/follow`, {
      method: 'DELETE',
    });
  },

  adminUploadProof: async (formData) => {
    return request('/admin/upload-proof', {
      method: 'POST',
      body: formData, // Since body is FormData, headers['Content-Type'] is omitted automatically by request()
    });
  },

  // Region Management (super-admin only)
  listRegions: async () => {
    return request('/admin/regions');
  },

  createRegion: async ({ name, type, parent_region_id }) => {
    return request('/admin/regions', {
      method: 'POST',
      body: { name, type, parent_region_id: parent_region_id || null },
    });
  },

  updateRegion: async (regionId, { name }) => {
    return request(`/admin/regions/${regionId}`, {
      method: 'PATCH',
      body: { name },
    });
  },

  assignAdminRegion: async (userId, { admin_scope, region_id }) => {
    return request(`/admin/users/${userId}/assign-region`, {
      method: 'POST',
      body: { admin_scope, region_id: region_id || null },
    });
  },
};


