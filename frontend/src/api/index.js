import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const message = error.response.data?.error || '请求失败'
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me')
}

// User API
export const userAPI = {
  getUser: (userId) => api.get(`/users/${userId}`),
  updateProfile: (data) => api.put('/users/profile', data),
  uploadAvatar: (formData) => api.post('/users/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  searchUsers: (keyword) => api.get('/users/search', { params: { keyword } })
}

// Post API
export const postAPI = {
  createPost: (data) => api.post('/posts', data),
  getPost: (postId) => api.get(`/posts/${postId}`),
  updatePost: (postId, data) => api.put(`/posts/${postId}`, data),
  deletePost: (postId) => api.delete(`/posts/${postId}`),
  getTimeline: (page) => api.get('/posts/timeline', { params: { page } }),
  getDiscover: (page) => api.get('/posts/discover', { params: { page } }),
  getUserPosts: (userId, page) => api.get(`/posts/user/${userId}`, { params: { page } })
}

// Comment API
export const commentAPI = {
  createComment: (data) => api.post('/comments', data),
  getPostComments: (postId, page) => api.get(`/comments/post/${postId}`, { params: { page } }),
  deleteComment: (commentId) => api.delete(`/comments/${commentId}`)
}

// Like API
export const likeAPI = {
  likePost: (postId) => api.post(`/likes/post/${postId}`),
  unlikePost: (postId) => api.delete(`/likes/post/${postId}`),
  getPostLikeStatus: (postId) => api.get(`/likes/post/${postId}/status`),
  likeComment: (commentId) => api.post(`/likes/comment/${commentId}`),
  unlikeComment: (commentId) => api.delete(`/likes/comment/${commentId}`)
}

// Follow API
export const followAPI = {
  follow: (userId) => api.post(`/follows/${userId}`),
  unfollow: (userId) => api.delete(`/follows/${userId}`),
  getFollowStatus: (userId) => api.get(`/follows/${userId}/status`),
  getFollowers: (userId, page) => api.get(`/follows/followers/${userId}`, { params: { page } }),
  getFollowing: (userId, page) => api.get(`/follows/following/${userId}`, { params: { page } })
}

// Notification API
export const notificationAPI = {
  getNotifications: (page, unreadOnly) => api.get('/notifications', { params: { page, unread_only: unreadOnly } }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (notificationId) => api.put(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.put('/notifications/read-all')
}

export default api
