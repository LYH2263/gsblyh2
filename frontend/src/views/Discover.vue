<template>
  <div class="discover">
    <!-- 搜索框 -->
    <div class="card">
      <div class="search-box">
        <input
          v-model="searchKeyword"
          type="text"
          class="form-input"
          placeholder="搜索用户、内容..."
          @keyup.enter="handleSearch"
        />
        <button class="btn btn-primary" @click="handleSearch">搜索</button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searching">
      <div class="card">
        <div class="card-title">搜索用户</div>
        <div v-if="searchUsers.length === 0" class="empty-state" style="padding: 20px;">
          未找到相关用户
        </div>
        <div v-else>
          <div
            v-for="u in searchUsers"
            :key="u.id"
            class="user-card"
            @click="router.push(`/profile/${u.id}`)"
          >
            <img :src="u.avatar || '/default-avatar.png'" class="avatar" />
            <div class="user-info">
              <div class="user-name">{{ u.nickname || u.username }}</div>
              <div class="user-bio">@{{ u.username }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 热门内容 -->
    <div v-else>
      <div class="card">
        <div class="card-title">热门微博</div>
      </div>

      <div class="posts-list">
        <div v-if="loading && posts.length === 0" class="loading">加载中...</div>
        <div v-else-if="posts.length === 0" class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>暂无内容</p>
        </div>
        <PostItem
          v-for="post in posts"
          :key="post.id"
          :post="post"
          @refresh="fetchPosts"
        />
        <div v-if="loading && posts.length > 0" class="loading">加载中...</div>
        <div v-if="!loading && hasMore" class="loading" style="cursor: pointer;" @click="loadMore">
          点击加载更多
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { postAPI, userAPI } from '../api'
import PostItem from '../components/PostItem.vue'

const router = useRouter()
const posts = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const searching = ref(false)
const searchKeyword = ref('')
const searchUsers = ref([])

async function fetchPosts() {
  loading.value = true
  try {
    const res = await postAPI.getDiscover(page.value)
    if (page.value === 1) {
      posts.value = res.posts
    } else {
      posts.value = [...posts.value, ...res.posts]
    }
    hasMore.value = res.page < res.pages
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  page.value++
  fetchPosts()
}

async function handleSearch() {
  if (!searchKeyword.value.trim()) {
    searching.value = false
    return
  }

  searching.value = true
  try {
    const res = await userAPI.searchUsers(searchKeyword.value)
    searchUsers.value = res.users || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.search-box {
  display: flex;
  gap: 10px;
}

.search-box .form-input {
  flex: 1;
}
</style>
