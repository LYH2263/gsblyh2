<template>
  <div class="notifications">
    <div class="card">
      <div class="tabs">
        <div
          class="tab"
          :class="{ active: !unreadOnly }"
          @click="unreadOnly = false; fetchNotifications()"
        >
          全部
        </div>
        <div
          class="tab"
          :class="{ active: unreadOnly }"
          @click="unreadOnly = true; fetchNotifications()"
        >
          未读
        </div>
        <button
          v-if="unreadCount > 0"
          class="btn btn-sm btn-outline"
          style="margin-left: auto;"
          @click="markAllRead"
        >
          全部标记已读
        </button>
      </div>

      <div v-if="loading && notifications.length === 0" class="loading">加载中...</div>
      <div v-else-if="notifications.length === 0" class="empty-state">
        <div class="empty-state-icon">🔔</div>
        <p>暂无通知</p>
      </div>
      <div v-else>
        <div
          v-for="n in notifications"
          :key="n.id"
          class="notification-item"
          :class="{ unread: !n.is_read }"
          @click="handleNotificationClick(n)"
        >
          <img
            :src="n.source_user?.avatar || '/default-avatar.png'"
            class="avatar"
          />
          <div class="notification-content">
            <div class="notification-text">{{ n.content }}</div>
            <div class="notification-time">{{ formatTime(n.created_at) }}</div>
          </div>
          <div v-if="!n.is_read" class="unread-dot"></div>
        </div>
      </div>

      <div v-if="!loading && hasMore" class="loading" style="cursor: pointer;" @click="loadMore">
        点击加载更多
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationAPI } from '../api'

const router = useRouter()
const notifications = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const unreadOnly = ref(false)
const unreadCount = ref(0)

async function fetchNotifications() {
  loading.value = true
  page.value = 1
  try {
    const res = await notificationAPI.getNotifications(page.value, unreadOnly.value)
    notifications.value = res.notifications
    unreadCount.value = res.unread_count
    hasMore.value = res.page < res.pages
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  page.value++
  loading.value = true
  try {
    const res = await notificationAPI.getNotifications(page.value, unreadOnly.value)
    notifications.value = [...notifications.value, ...res.notifications]
    hasMore.value = res.page < res.pages
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleNotificationClick(notification) {
  if (!notification.is_read) {
    try {
      await notificationAPI.markAsRead(notification.id)
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (e) {
      console.error(e)
    }
  }

  // 跳转到相关帖子
  if (notification.source_post_id) {
    router.push(`/profile/${notification.user_id}`)
  }
}

async function markAllRead() {
  try {
    await notificationAPI.markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (e) {
    console.error(e)
  }
}

function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.notification-item {
  position: relative;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: #e6162d;
  border-radius: 50%;
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
}
</style>
