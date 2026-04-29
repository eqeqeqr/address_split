<template>
  <div>
    <PageHeader title="环境配置" subtitle="配置地址拆分服务运行所需的 Redis 连接环境" />

    <section class="card section-card environment-card">
      <div class="env-heading">
        <div>
          <h2>Redis 配置</h2>
          <p>支持本地 Redis 和远程 Redis，保存后后端会使用该配置读写拆分缓存与记录。</p>
        </div>
        <span class="env-badge">{{ activeRedisLabel }}</span>
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

      <div class="active-redis-banner" :class="activeConfig.mode">
        <span class="active-pulse" />
        <div>
          <strong>当前激活：{{ activeRedisLabel }}</strong>
          <p>{{ activeConfig.host || '未填写 Host' }}:{{ activeConfig.port || '-' }} / DB {{ activeConfig.db ?? 0 }}</p>
          <small v-if="form.mode !== activeConfig.mode">
            正在编辑{{ editingRedisLabel }}，保存配置后才会切换激活 Redis。
          </small>
        </div>
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

      <div class="env-actions">
        <div v-if="message" class="env-message" :class="{ success: testOk, danger: !testOk }">
          <span class="message-dot" />
          <span>{{ message }}</span>
        </div>
        <div v-else class="env-message-placeholder">点击按钮后会在这里显示操作结果</div>

        <button type="button" class="ghost-button" :disabled="loading || testing" @click="resetConfig">
          {{ loading ? '重置中...' : '重置' }}
        </button>
        <button type="button" class="secondary-button" :disabled="loading || testing" @click="testConfig">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <button type="button" class="primary-button" :disabled="loading || saving" @click="saveConfig">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </section>

    <div v-if="message" class="env-toast" :class="{ success: testOk, danger: !testOk }">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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
let toastTimer: number | undefined

const form = reactive<RedisConfig>({
  mode: 'local',
  host: '127.0.0.1',
  port: 6379,
  db: 0,
  password: '',
  updatedAt: '',
})

const activeConfig = reactive<RedisConfig>({
  mode: 'local',
  host: '127.0.0.1',
  port: 6379,
  db: 0,
  password: '',
  updatedAt: '',
})

const activeRedisLabel = computed(() => (activeConfig.mode === 'local' ? '本地 Redis' : '远程 Redis'))
const editingRedisLabel = computed(() => (form.mode === 'local' ? '本地 Redis' : '远程 Redis'))

const applyConfig = (config: RedisConfig) => {
  form.mode = config.mode
  form.host = config.host
  form.port = config.port
  form.db = config.db
  form.password = config.password ?? ''
  form.updatedAt = config.updatedAt ?? ''
}

const applyActiveConfig = (config: RedisConfig) => {
  activeConfig.mode = config.mode
  activeConfig.host = config.host
  activeConfig.port = config.port
  activeConfig.db = config.db
  activeConfig.password = config.password ?? ''
  activeConfig.updatedAt = config.updatedAt ?? ''
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

const showMessage = (text: string, ok: boolean) => {
  testOk.value = ok
  message.value = text
  if (toastTimer !== undefined) {
    window.clearTimeout(toastTimer)
  }
  toastTimer = window.setTimeout(() => {
    message.value = ''
    toastTimer = undefined
  }, 5000)
}

const setMode = (mode: RedisConfig['mode']) => {
  form.mode = mode
  if (mode === 'local' && !form.host.trim()) {
    form.host = '127.0.0.1'
  }
}

const loadConfig = async (notify = false) => {
  loading.value = true
  try {
    const config = await getRedisConfig()
    applyConfig(config)
    applyActiveConfig(config)
    if (notify) {
      showMessage('Redis 配置已重置为本地保存值', true)
    }
  } catch (error) {
    showMessage(error instanceof Error ? error.message : '读取 Redis 配置失败', false)
  } finally {
    loading.value = false
  }
}

const resetConfig = () => {
  void loadConfig(true)
}

const testConfig = async () => {
  const error = validate()
  if (error) {
    showMessage(error, false)
    return
  }

  testing.value = true
  try {
    const result = await testRedisConfig({ ...form })
    showMessage(result.message, result.ok)
  } catch (err) {
    showMessage(err instanceof Error ? err.message : 'Redis 连接测试失败', false)
  } finally {
    testing.value = false
  }
}

const saveConfig = async () => {
  const error = validate()
  if (error) {
    showMessage(error, false)
    return
  }

  saving.value = true
  try {
    const saved = await saveRedisConfig({ ...form })
    applyConfig(saved)
    applyActiveConfig(saved)
    showMessage('Redis 配置已保存到本地 SQLite', true)
  } catch (err) {
    showMessage(err instanceof Error ? err.message : '保存 Redis 配置失败', false)
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.environment-card {
  max-width: 860px;
  width: 100%;
  box-sizing: border-box;
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
  margin-bottom: 14px;
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

.active-redis-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
  padding: 14px 16px;
  border: 1px solid rgba(31, 120, 255, 0.22);
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 100%);
}

.active-redis-banner.remote {
  border-color: rgba(245, 158, 11, 0.28);
  background: linear-gradient(180deg, #fffdf7 0%, #fff7e6 100%);
}

.active-redis-banner strong {
  color: #0f172a;
}

.active-redis-banner p {
  margin: 4px 0 0;
  color: var(--text-sub);
  font-size: 14px;
}

.active-redis-banner small {
  display: block;
  margin-top: 6px;
  color: #b45309;
  font-weight: 700;
}

.active-pulse {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: var(--success);
  box-shadow: 0 0 0 7px rgba(16, 185, 129, 0.12);
  flex: none;
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
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  margin-right: auto;
  font-weight: 700;
}

.env-message.success {
  color: var(--success);
}

.env-message.danger {
  color: var(--danger);
}

.message-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: currentColor;
  flex: none;
}

.env-message-placeholder {
  margin-right: auto;
  color: var(--text-muted);
  font-size: 14px;
}

.env-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  flex-wrap: wrap;
}

.env-toast {
  position: fixed;
  right: 28px;
  top: 24px;
  z-index: 100;
  max-width: min(420px, calc(100vw - 56px));
  padding: 14px 18px;
  border-radius: 14px;
  color: #0f172a;
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.16);
  font-weight: 700;
}

.env-toast.success {
  color: #047857;
  border-color: rgba(16, 185, 129, 0.35);
  background: #ecfdf5;
}

.env-toast.danger {
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.35);
  background: #fef2f2;
}
</style>
