<template>
  <div class="timeline">
    <!-- 发布框 -->
    <div class="card">
      <div class="post-editor">
        <img :src="authStore.user?.avatar || '/default-avatar.png'" class="avatar" />
        <div class="editor-content">
          <textarea
            v-model="newPost.content"
            class="form-input"
            placeholder="有什么新鲜事想分享给大家？"
            rows="3"
          ></textarea>
          <div class="editor-images" v-if="newPost.images.length">
            <div v-for="(img, idx) in newPost.images" :key="idx" class="editor-image">
              <img :src="img" />
              <span class="remove-btn" @click="removeImage(idx)">×</span>
            </div>
          </div>
          <div class="editor-actions">
            <div class="editor-tools">
              <label class="tool-btn">
                <input type="file" accept="image/*" multiple @change="handleImageSelect" hidden />
                <span>📷</span>
              </label>
            </div>
            <button
              class="btn btn-primary"
              :disabled="!newPost.content && !newPost.images.length || posting"
              @click="submitPost"
            >
              {{ posting ? '发布中...' : '发布' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子列表 -->
    <div class="posts-list">
      <div v-if="loading && posts.length === 0" class="loading">加载中...</div>
      <div v-else-if="posts.length === 0" class="empty-state">
        <div class="empty-state-icon">📭</div>
        <p>还没有关注的人？快去发现感兴趣的内容吧</p>
        <router-link to="/discover" class="btn btn-primary" style="margin-top: 20px;">
          发现更多
        </router-link>
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
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { postAPI } from '../api'
import { useAuthStore } from '../stores/auth'
import PostItem from '../components/PostItem.vue'

const authStore = useAuthStore()
const posts = ref([])
const loading = ref(false)
const posting = ref(false)
const page = ref(1)
const hasMore = ref(true)
const newPost = reactive({
  content: '',
  images: []
})

async function fetchPosts() {
  loading.value = true
  try {
    const res = await postAPI.getTimeline(page.value)
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

function handleImageSelect(e) {
  const files = Array.from(e.target.files)
  files.forEach(file => {
    if (newPost.images.length >= 9) return
    const reader = new FileReader()
    reader.onload = (event) => {
      newPost.images.push(event.target.result)
    }
    reader.readAsDataURL(file)
  })
}

function removeImage(idx) {
  newPost.images.splice(idx, 1)
}

async function submitPost() {
  if (!newPost.content && !newPost.images.length) return

  posting.value = true
  try {
    const formData = new FormData()
    formData.append('content', newPost.content)
    
    // Convert base64 to file objects
    for (const img of newPost.images) {
      if (img.startsWith('data:')) {
        const response = await fetch(img)
        const blob = await response.blob()
        const file = new File([blob], 'image.jpg', { type: blob.type })
        formData.append('images', file)
      } else {
        formData.append('images', img)
      }
    }
    
    await postAPI.createPost(formData)
    newPost.content = ''
    newPost.images = []
    await fetchPosts()
  } catch (e) {
    console.error(e)
  } finally {
    posting.value = false
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.post-editor {
  display: flex;
  gap: 15px;
}

.editor-content {
  flex: 1;
}

.editor-content .form-input {
  border: none;
  padding: 10px 0;
  resize: none;
}

.editor-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.editor-image {
  position: relative;
  width: 80px;
  height: 80px;
}

.editor-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.editor-image .remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
}

.editor-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.editor-tools {
  display: flex;
  gap: 15px;
}

.tool-btn {
  cursor: pointer;
  font-size: 20px;
}

.tool-btn:hover {
  opacity: 0.8;
}
</style>
