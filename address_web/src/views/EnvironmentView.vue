<template>
  <div>
    <PageHeader title="环境配置" subtitle="配置地址拆分服务运行所需的 Redis 连接环境" />

    <section class="card section-card environment-card">
      <div class="env-heading">
        <div>
          <h2>Redis 配置</h2>
          <p>支持本地 Redis 和远程 Redis，保存后后端会使用该配置读写拆分缓存与记录。</p>
        </div>
        <span class="env-badge">{{ form.mode === 'local' ? '本地连接' : '远程连接' }}</span>
      </div>

      <div class="mode-switch">
        <button
          type="button"
          class="mode-button"
          :class="{ active: form.mode === 'local' }"
          @click="setMode('local')"
        >
          本地 Redis
        </button>
        <button
          type="button"
          class="mode-button"
          :class="{ active: form.mode === 'remote' }"
          @click="setMode('remote')"
        >
          远程 Redis
        </button>
      </div>

      <div class="env-form">
        <label>
          <span class="field-label">Host</span>
          <input v-model="form.host" class="input" placeholder="127.0.0.1" />
        </label>

        <label>
          <span class="field-label">Port</span>
          <input v-model.number="form.port" class="input" min="1" max="65535" type="number" />
        </label>

        <label>
          <span class="field-label">DB</span>
          <input v-model.number="form.db" class="input" min="0" type="number" />
        </label>

        <label>
          <span class="field-label">Password</span>
          <input v-model="form.password" class="input" placeholder="无密码可留空" type="password" />
        </label>
      </div>

      <p v-if="form.updatedAt" class="muted">上次保存：{{ form.updatedAt }}</p>
      <p v-if="message" class="env-message" :class="{ success: testOk, danger: !testOk }">{{ message }}</p>

      <div class="env-actions">
        <button type="button" class="ghost-button" :disabled="loading || testing" @click="loadConfig">重置</button>
        <button type="button" class="secondary-button" :disabled="loading || testing" @click="testConfig">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <button type="button" class="primary-button" :disabled="loading || saving" @click="saveConfig">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  getRedisConfig,
  saveRedisConfig,
  testRedisConfig,
  type RedisConfig,
} from '../api/address'
import PageHeader from '../components/PageHeader.vue'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testOk = ref(false)
const message = ref('')

const form = reactive<RedisConfig>({
  mode: 'local',
  host: '127.0.0.1',
  port: 6379,
  db: 0,
  password: '',
  updatedAt: '',
})

const applyConfig = (config: RedisConfig) => {
  form.mode = config.mode
  form.host = config.host
  form.port = config.port
  form.db = config.db
  form.password = config.password ?? ''
  form.updatedAt = config.updatedAt ?? ''
}

const validate = () => {
  if (!form.host.trim()) {
    return 'Host 不能为空'
  }
  if (!Number.isInteger(Number(form.port)) || Number(form.port) < 1 || Number(form.port) > 65535) {
    return 'Port 必须在 1 到 65535 之间'
  }
  if (!Number.isInteger(Number(form.db)) || Number(form.db) < 0) {
    return 'DB 必须是大于等于 0 的整数'
  }
  return ''
}

const setMode = (mode: RedisConfig['mode']) => {
  form.mode = mode
  if (mode === 'local' && !form.host.trim()) {
    form.host = '127.0.0.1'
  }
}

const loadConfig = async () => {
  loading.value = true
  message.value = ''
  try {
    applyConfig(await getRedisConfig())
  } catch (error) {
    testOk.value = false
    message.value = error instanceof Error ? error.message : '读取 Redis 配置失败'
  } finally {
    loading.value = false
  }
}

const testConfig = async () => {
  const error = validate()
  if (error) {
    testOk.value = false
    message.value = error
    return
  }

  testing.value = true
  message.value = ''
  try {
    const result = await testRedisConfig({ ...form })
    testOk.value = result.ok
    message.value = result.message
  } catch (err) {
    testOk.value = false
    message.value = err instanceof Error ? err.message : 'Redis 连接测试失败'
  } finally {
    testing.value = false
  }
}

const saveConfig = async () => {
  const error = validate()
  if (error) {
    testOk.value = false
    message.value = error
    return
  }

  saving.value = true
  message.value = ''
  try {
    applyConfig(await saveRedisConfig({ ...form }))
    testOk.value = true
    message.value = 'Redis 配置已保存到本地 SQLite'
  } catch (err) {
    testOk.value = false
    message.value = err instanceof Error ? err.message : '保存 Redis 配置失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.environment-card {
  max-width: 860px;
}

.env-heading {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.env-heading h2 {
  margin: 0;
  font-size: 22px;
}

.env-heading p {
  margin: 8px 0 0;
  color: var(--text-sub);
}

.env-badge {
  padding: 8px 12px;
  border-radius: 999px;
  color: #0f5bd7;
  background: #edf4ff;
  font-weight: 700;
}

.mode-switch {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 14px;
  background: #f1f5f9;
  margin-bottom: 22px;
}

.mode-button {
  padding: 10px 18px;
  border-radius: 10px;
  color: #475569;
  font-weight: 700;
  cursor: pointer;
}

.mode-button.active {
  color: var(--primary);
  background: #fff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.env-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.env-form label {
  display: grid;
  gap: 8px;
}

.env-message {
  margin: 18px 0 0;
  font-weight: 700;
}

.env-message.success {
  color: var(--success);
}

.env-message.danger {
  color: var(--danger);
}

.env-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
