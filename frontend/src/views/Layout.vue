<template>
  <div class="layout">
    <!-- Header -->
    <header class="header">
      <div class="container header-content">
        <router-link to="/timeline" class="logo">微博</router-link>

        <nav class="nav-menu">
          <router-link
            to="/timeline"
            class="nav-item"
            :class="{ active: route.path === '/timeline' }"
          >
            首页
          </router-link>
          <router-link
            to="/discover"
            class="nav-item"
            :class="{ active: route.path === '/discover' }"
          >
            发现
          </router-link>
        </nav>

        <div class="header-right">
          <el-badge :value="unreadCount" :hidden="!unreadCount" :max="99">
            <router-link to="/notifications" class="nav-item">
              <span style="font-size: 20px;">🔔</span>
            </router-link>
          </el-badge>

          <el-dropdown trigger="click" @command="handleCommand">
            <img :src="user?.avatar || '/default-avatar.png'" class="avatar" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="`/profile/${user?.id}`">
                  个人主页
                </el-dropdown-item>
                <el-dropdown-item command="profile-edit">编辑资料</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-layout">
      <aside class="sidebar">
        <div class="card">
          <router-link :to="`/profile/${user?.id}`" class="user-card">
            <img :src="user?.avatar || '/default-avatar.png'" class="avatar" />
            <div class="user-info">
              <div class="user-name">{{ user?.nickname || user?.username }}</div>
              <div class="user-bio">{{ user?.bio || '暂无简介' }}</div>
            </div>
          </router-link>
        </div>

        <div class="card">
          <div class="profile-stats" style="justify-content: center;">
            <div class="profile-stat" @click="router.push(`/profile/${user?.id}?tab=following`)">
              <div class="profile-stat-value">{{ user?.following_count || 0 }}</div>
              <div class="profile-stat-label">关注</div>
            </div>
            <div class="profile-stat" @click="router.push(`/profile/${user?.id}?tab=followers`)">
              <div class="profile-stat-value">{{ user?.followers_count || 0 }}</div>
              <div class="profile-stat-label">粉丝</div>
            </div>
            <div class="profile-stat" @click="router.push(`/profile/${user?.id}`)">
              <div class="profile-stat-value">{{ user?.posts_count || 0 }}</div>
              <div class="profile-stat-label">微博</div>
            </div>
          </div>
        </div>

        <div class="card">
          <router-link to="/profile/edit" class="btn btn-outline" style="width: 100%;">
            编辑资料
          </router-link>
        </div>
      </aside>

      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { notificationAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const unreadCount = ref(0)

async function fetchUnreadCount() {
  try {
    const res = await notificationAPI.getUnreadCount()
    unreadCount.value = res.unread_count
  } catch (e) {
    console.error(e)
  }
}

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  } else {
    router.push(command)
  }
}

onMounted(() => {
  fetchUnreadCount()
  // 定期检查未读通知
  setInterval(fetchUnreadCount, 60000)
})
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.sidebar .user-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.sidebar .user-info {
  margin-left: 10px;
}

.sidebar .user-name {
  font-weight: 600;
  color: #333;
}

.sidebar .user-bio {
  font-size: 12px;
  color: #999;
}
</style>
