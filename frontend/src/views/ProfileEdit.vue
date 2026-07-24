<template>
  <div class="profile-edit">
    <div class="card">
      <div class="card-title">编辑资料</div>

      <div class="form-group">
        <label class="form-label">头像</label>
        <div class="avatar-upload">
          <img :src="previewAvatar || authStore.user?.avatar || '/default-avatar.png'" class="avatar-lg" />
          <label class="btn btn-outline" style="margin-left: 20px;">
            选择图片
            <input type="file" accept="image/*" @change="handleAvatarChange" hidden />
          </label>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">昵称</label>
        <input
          v-model="form.nickname"
          type="text"
          class="form-input"
          placeholder="请输入昵称"
          maxlength="20"
        />
      </div>

      <div class="form-group">
        <label class="form-label">简介</label>
        <textarea
          v-model="form.bio"
          class="form-input"
          placeholder="请输入个人简介"
          maxlength="200"
          rows="3"
        ></textarea>
        <div style="text-align: right; font-size: 12px; color: #999;">
          {{ form.bio.length }}/200
        </div>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="success" class="success-message">{{ success }}</div>

      <div style="display: flex; gap: 10px;">
        <button class="btn btn-primary" :loading="saving" @click="handleSave">
          保存
        </button>
        <button class="btn btn-outline" @click="router.back()">
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { userAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  nickname: '',
  bio: ''
})
const previewAvatar = ref('')
const avatarFile = ref(null)
const saving = ref(false)
const error = ref('')
const success = ref('')

function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return

  avatarFile.value = file
  const reader = new FileReader()
  reader.onload = (event) => {
    previewAvatar.value = event.target.result
  }
  reader.readAsDataURL(file)
}

async function handleSave() {
  error.value = ''
  success.value = ''
  saving.value = true

  try {
    // 先上传头像
    if (avatarFile.value) {
      const formData = new FormData()
      formData.append('avatar', avatarFile.value)
      await userAPI.uploadAvatar(formData)
    }

    // 更新资料
    await userAPI.updateProfile({
      nickname: form.nickname,
      bio: form.bio
    })

    // 刷新用户信息
    await authStore.fetchCurrentUser()
    ElMessage.success('保存成功')
    router.push(`/profile/${authStore.user?.id}`)
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  form.nickname = authStore.user?.nickname || ''
  form.bio = authStore.user?.bio || ''
})
</script>

<style scoped>
.avatar-upload {
  display: flex;
  align-items: center;
}

.success-message {
  color: #4caf50;
  font-size: 14px;
  margin-bottom: 15px;
}
</style>
