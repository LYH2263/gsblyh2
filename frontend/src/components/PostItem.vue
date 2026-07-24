<template>
  <div class="post-item">
    <div class="post-header">
      <router-link :to="`/profile/${post.author?.id}`">
        <img :src="post.author?.avatar || '/default-avatar.png'" class="avatar" />
      </router-link>
      <div class="post-author-info">
        <router-link :to="`/profile/${post.author?.id}`" class="post-author-name">
          {{ post.author?.nickname || post.author?.username }}
        </router-link>
        <div class="post-time">{{ formatTime(post.created_at) }}</div>
      </div>
      <div v-if="!isOwn && post.author" class="follow-btn-wrapper">
        <button
          v-if="following"
          class="btn btn-sm btn-outline"
          @click="handleUnfollow"
        >
          已关注
        </button>
        <button
          v-else
          class="btn btn-sm btn-primary"
          @click="handleFollow"
        >
          关注
        </button>
      </div>
      <el-dropdown v-if="isOwn" trigger="click" @command="handleCommand">
        <span class="more-btn">···</span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="edit">编辑</el-dropdown-item>
            <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="post-content" @click="showDetail">
      {{ post.content }}
    </div>

    <div
      v-if="images.length"
      class="post-images"
      :class="imageClass"
      @click="showDetail"
    >
      <img
        v-for="(img, idx) in images"
        :key="idx"
        :src="img"
        class="post-image"
      />
    </div>

    <div class="post-actions">
      <div class="post-action" :class="{ active: liked }" @click="toggleLike">
        <span>{{ liked ? '❤️' : '🤍' }}</span>
        <span>{{ likeCount }}</span>
      </div>
      <div class="post-action" @click="showComment = !showComment">
        <span>💬</span>
        <span>{{ post.comments_count }}</span>
      </div>
    </div>

    <!-- 评论区域 -->
    <div v-if="showComment" class="comment-section">
      <!-- 评论输入框 -->
      <div class="comment-input">
        <img :src="authStore.user?.avatar || '/default-avatar.png'" class="avatar avatar-sm" />
        <input
          v-model="commentContent"
          type="text"
          class="form-input"
          placeholder="写评论..."
          @keyup.enter="submitComment"
        />
        <button class="btn btn-sm btn-primary" @click="submitComment">发布</button>
      </div>

      <!-- 评论列表 -->
      <div v-if="loadingComments" class="loading">加载中...</div>
      <div v-else-if="comments.length === 0" class="empty-state" style="padding: 20px;">
        暂无评论
      </div>
      <div v-else>
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <div style="display: flex; align-items: flex-start;">
            <router-link :to="`/profile/${comment.author?.id}`">
              <img :src="comment.author?.avatar || '/default-avatar.png'" class="avatar avatar-sm" />
            </router-link>
            <div style="flex: 1; margin-left: 10px;">
              <div>
                <router-link :to="`/profile/${comment.author?.id}`" style="font-weight: 600;">
                  {{ comment.author?.nickname || comment.author?.username }}
                </router-link>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
              <div class="post-time">{{ formatTime(comment.created_at) }}</div>
            </div>
          </div>

          <!-- 评论的回复 -->
          <div v-if="comment.replies && comment.replies.length" class="comment-replies">
            <div v-for="reply in comment.replies" :key="reply.id" class="comment-item">
              <div style="display: flex; align-items: flex-start;">
                <router-link :to="`/profile/${reply.author?.id}`">
                  <img :src="reply.author?.avatar || '/default-avatar.png'" class="avatar avatar-sm" />
                </router-link>
                <div style="flex: 1; margin-left: 10px;">
                  <div>
                    <router-link :to="`/profile/${reply.author?.id}`" style="font-weight: 600;">
                      {{ reply.author?.nickname || reply.author?.username }}
                    </router-link>
                  </div>
                  <div class="comment-content">{{ reply.content }}</div>
                  <div class="post-time">{{ formatTime(reply.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEdit" title="编辑微博" width="500px">
      <textarea
        v-model="editContent"
        class="form-input"
        rows="4"
      ></textarea>
      <template #footer>
        <button class="btn btn-outline" @click="showEdit = false">取消</button>
        <button class="btn btn-primary" @click="handleUpdate">保存</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { postAPI, likeAPI, commentAPI, followAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const authStore = useAuthStore()
const showComment = ref(false)
const commentContent = ref('')
const comments = ref([])
const loadingComments = ref(false)
const liked = ref(false)
const likeCount = ref(props.post.likes_count || 0)
const showEdit = ref(false)
const editContent = ref('')
const following = ref(false)

const images = computed(() => {
  if (!props.post.images) return []
  try {
    return JSON.parse(props.post.images)
  } catch {
    return []
  }
})

const imageClass = computed(() => {
  const count = images.value.length
  if (count === 1) return 'single'
  if (count === 2) return 'double'
  return 'multi'
})

const isOwn = computed(() => props.post.author?.id === authStore.user?.id)

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

function showDetail() {
  // 可以跳转到详情页
}

async function fetchComments() {
  loadingComments.value = true
  try {
    const res = await commentAPI.getPostComments(props.post.id)
    comments.value = res.comments || []
  } catch (e) {
    console.error(e)
  } finally {
    loadingComments.value = false
  }
}

async function fetchLikeStatus() {
  try {
    const res = await likeAPI.getPostLikeStatus(props.post.id)
    liked.value = res.liked
    likeCount.value = res.likes_count
  } catch (e) {
    console.error(e)
  }
}

async function fetchFollowStatus() {
  if (isOwn.value || !post.author?.id) return
  try {
    const res = await followAPI.getFollowStatus(post.author.id)
    following.value = res.following
  } catch (e) {
    console.error(e)
  }
}

async function handleFollow() {
  try {
    await followAPI.follow(post.author.id)
    following.value = true
    ElMessage.success('关注成功')
  } catch (e) {
    ElMessage.error(e.message || '关注失败')
  }
}

async function handleUnfollow() {
  try {
    await followAPI.unfollow(post.author.id)
    following.value = false
    ElMessage.success('取消关注成功')
  } catch (e) {
    ElMessage.error(e.message || '取消关注失败')
  }
}

async function toggleLike() {
  try {
    if (liked.value) {
      await likeAPI.unlikePost(props.post.id)
      likeCount.value--
    } else {
      await likeAPI.likePost(props.post.id)
      likeCount.value++
    }
    liked.value = !liked.value
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function submitComment() {
  if (!commentContent.value.trim()) return

  try {
    await commentAPI.createComment({
      post_id: props.post.id,
      content: commentContent.value
    })
    commentContent.value = ''
    await fetchComments()
    ElMessage.success('评论成功')
  } catch (e) {
    ElMessage.error(e.message || '评论失败')
  }
}

function handleCommand(command) {
  if (command === 'edit') {
    editContent.value = props.post.content
    showEdit.value = true
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定要删除这条微博吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        await postAPI.deletePost(props.post.id)
        ElMessage.success('删除成功')
        emit('refresh')
      } catch (e) {
        ElMessage.error(e.message || '删除失败')
      }
    }).catch(() => {})
  }
}

async function handleUpdate() {
  try {
    await postAPI.updatePost(props.post.id, { content: editContent.value })
    showEdit.value = false
    ElMessage.success('更新成功')
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message || '更新失败')
  }
}

onMounted(() => {
  fetchLikeStatus()
  fetchFollowStatus()
})
</script>

<style scoped>
.post-item {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.follow-btn-wrapper {
  margin-left: auto;
}

.post-author-info {
  margin-left: 10px;
  flex: 1;
}

.post-author-name {
  font-weight: 600;
  color: #333;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.more-btn {
  cursor: pointer;
  padding: 5px;
  font-size: 18px;
  color: #999;
}

.comment-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.comment-input {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 15px;
}

.comment-input .form-input {
  flex: 1;
}
</style>
