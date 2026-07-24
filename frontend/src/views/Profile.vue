<template>
  <div class="profile-page">
    <div v-if="loading && !user" class="loading">加载中...</div>
    <div v-else-if="!user" class="empty-state">用户不存在</div>
    <template v-else>
      <!-- 个人资料头部 -->
      <div class="profile-header">
        <div class="profile-banner"></div>
        <div class="profile-info">
          <div class="profile-actions">
            <img
              :src="user.avatar || '/default-avatar.png'"
              class="profile-avatar"
            />
            <div v-if="!isOwn" class="action-buttons">
              <button
                v-if="followStatus.following"
                class="btn btn-outline"
                @click="handleUnfollow"
              >
                已关注
              </button>
              <button
                v-else
                class="btn btn-primary"
                @click="handleFollow"
              >
                关注
              </button>
            </div>
          </div>
          <div class="profile-name">{{ user.nickname || user.username }}</div>
          <div class="profile-username">@{{ user.username }}</div>
          <div class="profile-bio">{{ user.bio || '暂无简介' }}</div>
          <div class="profile-stats">
            <div class="profile-stat" @click="tab = 'posts'">
              <div class="profile-stat-value">{{ user.posts_count }}</div>
              <div class="profile-stat-label">微博</div>
            </div>
            <div class="profile-stat" @click="tab = 'followers'">
              <div class="profile-stat-value">{{ user.followers_count }}</div>
              <div class="profile-stat-label">粉丝</div>
            </div>
            <div class="profile-stat" @click="tab = 'following'">
              <div class="profile-stat-value">{{ user.following_count }}</div>
              <div class="profile-stat-label">关注</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="tabs">
        <div class="tab" :class="{ active: tab === 'posts' }" @click="tab = 'posts'">
          微博
        </div>
        <div class="tab" :class="{ active: tab === 'followers' }" @click="tab = 'followers'">
          粉丝
        </div>
        <div class="tab" :class="{ active: tab === 'following' }" @click="tab = 'following'">
          关注
        </div>
      </div>

      <!-- 微博列表 -->
      <div v-if="tab === 'posts'">
        <div v-if="loadingPosts" class="loading">加载中...</div>
        <div v-else-if="posts.length === 0" class="empty-state">
          <div class="empty-state-icon">📝</div>
          <p>还没有发布过微博</p>
        </div>
        <PostItem
          v-for="post in posts"
          :key="post.id"
          :post="post"
          @refresh="fetchPosts"
        />
        <div v-if="hasMorePosts" class="loading" style="cursor: pointer;" @click="loadMorePosts">
          点击加载更多
        </div>
      </div>

      <!-- 粉丝列表 -->
      <div v-else-if="tab === 'followers'">
        <div v-if="loadingList" class="loading">加载中...</div>
        <div v-else-if="userList.length === 0" class="empty-state">
          暂无{{ tab === 'followers' ? '粉丝' : '关注' }}
        </div>
        <div v-else>
          <div
            v-for="u in userList"
            :key="u.id"
            class="user-card"
            @click="router.push(`/profile/${u.id}`)"
          >
            <img :src="u.avatar || '/default-avatar.png'" class="avatar" />
            <div class="user-info">
              <div class="user-name">{{ u.nickname || u.username }}</div>
              <div class="user-bio">{{ u.bio || '@' + u.username }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 关注列表 -->
      <div v-else-if="tab === 'following'">
        <div v-if="loadingList" class="loading">加载中...</div>
        <div v-else-if="userList.length === 0" class="empty-state">
          暂无关注
        </div>
        <div v-else>
          <div
            v-for="u in userList"
            :key="u.id"
            class="user-card"
            @click="router.push(`/profile/${u.id}`)"
          >
            <img :src="u.avatar || '/default-avatar.png'" class="avatar" />
            <div class="user-info">
              <div class="user-name">{{ u.nickname || u.username }}</div>
              <div class="user-bio">{{ u.bio || '@' + u.username }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { userAPI, postAPI, followAPI } from '../api'
import PostItem from '../components/PostItem.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const user = ref(null)
const loading = ref(true)
const posts = ref([])
const loadingPosts = ref(false)
const postPage = ref(1)
const hasMorePosts = ref(true)
const tab = ref('posts')
const userList = ref([])
const loadingList = ref(false)
const followStatus = ref({ following: false })

const isOwn = computed(() => user.value?.id === authStore.user?.id)

async function fetchUser() {
  loading.value = true
  const userId = route.params.userId || authStore.user?.id
  try {
    const res = await userAPI.getUser(userId)
    user.value = res.user
    if (!isOwn.value) {
      const status = await followAPI.getFollowStatus(userId)
      followStatus.value = status
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchPosts() {
  loadingPosts.value = true
  const userId = route.params.userId || authStore.user?.id
  try {
    const res = await postAPI.getUserPosts(userId, postPage.value)
    if (postPage.value === 1) {
      posts.value = res.posts
    } else {
      posts.value = [...posts.value, ...res.posts]
    }
    hasMorePosts.value = res.page < res.pages
  } catch (e) {
    console.error(e)
  } finally {
    loadingPosts.value = false
  }
}

function loadMorePosts() {
  postPage.value++
  fetchPosts()
}

async function fetchUserList() {
  loadingList.value = true
  const userId = route.params.userId || authStore.user?.id
  try {
    let res
    if (tab.value === 'followers') {
      res = await followAPI.getFollowers(userId, 1)
    } else {
      res = await followAPI.getFollowing(userId, 1)
    }
    userList.value = res.followers || res.following || []
  } catch (e) {
    console.error(e)
  } finally {
    loadingList.value = false
  }
}

async function handleFollow() {
  try {
    await followAPI.follow(user.value.id)
    followStatus.value.following = true
    user.value.followers_count++
  } catch (e) {
    console.error(e)
  }
}

async function handleUnfollow() {
  try {
    await followAPI.unfollow(user.value.id)
    followStatus.value.following = false
    user.value.followers_count--
  } catch (e) {
    console.error(e)
  }
}

watch(tab, (newTab) => {
  if (newTab === 'posts') {
    fetchPosts()
  } else {
    fetchUserList()
  }
})

watch(() => route.params.userId, () => {
  postPage.value = 1
  fetchUser()
  fetchPosts()
})

onMounted(() => {
  if (route.query.tab) {
    tab.value = route.query.tab
  }
  fetchUser()
  if (tab.value === 'posts') {
    fetchPosts()
  } else {
    fetchUserList()
  }
})
</script>

<style scoped>
.profile-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.action-buttons {
  margin-bottom: 10px;
}
</style>
