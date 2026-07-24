import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      {
        path: '',
        redirect: '/timeline'
      },
      {
        path: 'timeline',
        name: 'timeline',
        component: () => import('../views/Timeline.vue')
      },
      {
        path: 'discover',
        name: 'discover',
        component: () => import('../views/Discover.vue')
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('../views/Notifications.vue')
      },
      {
        path: 'profile/:userId?',
        name: 'profile',
        component: () => import('../views/Profile.vue')
      },
      {
        path: 'profile/edit',
        name: 'profile-edit',
        component: () => import('../views/ProfileEdit.vue')
      }
    ],
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    next('/timeline')
  } else {
    next()
  }
})

export default router
