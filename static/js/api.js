const API = {
  baseUrl: '',

  // Token Management
  getToken()  { return localStorage.getItem('access_token'); },
  getRole()   { return localStorage.getItem('user_role'); },
  getName()   { return localStorage.getItem('user_name'); },
  getId()     { return localStorage.getItem('user_id'); },

  isLoggedIn() { return !!this.getToken(); },

  logout() {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      fetch('/api/auth/logout/', {
        method: 'POST',
        headers: this.authHeaders(),
        body: JSON.stringify({ refresh }),
      }).catch(() => {});
    }
    localStorage.clear();
    window.location.href = '/accounts/login/';
  },

  authHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`,
    };
  },

  // Generic Request 
  async request(url, options = {}) {
    const res = await fetch(url, {
      ...options,
      headers: { ...this.authHeaders(), ...(options.headers || {}) },
    });

    if (res.status === 401) {
      // Token expired — try refresh
      const refreshed = await this.refreshToken();
      if (refreshed) {
        // Retry original request
        return fetch(url, {
          ...options,
          headers: { ...this.authHeaders(), ...(options.headers || {}) },
        });
      } else {
        this.logout();
        return null;
      }
    }
    return res;
  },

  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    try {
      const res  = await fetch('/api/auth/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('access_token', data.access);
        return true;
      }
    } catch (e) {}
    return false;
  },

  // Profile
  async getProfile() {
    const res = await this.request('/api/auth/profile/');
    return res?.ok ? res.json() : null;
  },

  //Auth Guard
  requireAuth(expectedRole = null) {
    if (!this.isLoggedIn()) {
      window.location.href = '/accounts/login/';
      return false;
    }
    if (expectedRole && this.getRole() !== expectedRole) {
      const role = this.getRole();
      if (role === 'admin')  window.location.href = '/dashboard/admin/';
      else if (role === 'driver') window.location.href = '/dashboard/driver/';
      else window.location.href = '/dashboard/user/';
      return false;
    }
    return true;
  },
};
