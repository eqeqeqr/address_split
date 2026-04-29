<template>
  <div>
    <PageHeader
      title="自定义场景"
      subtitle="管理地址中的场景正则规则，系统默认规则也支持编辑和删除，可通过重置按钮补回缺失项"
    />

    <section class="card section-card">
      <div class="toolbar scene-toolbar">
        <TabSwitcher v-model="activeTab" :tabs="sceneTabs" compact />
        <div class="toolbar-spacer" />
        <button type="button" class="secondary-button" :disabled="isResetting" @click="resetDefaults">
          {{ isResetting ? '重置中...' : '重置系统默认' }}
        </button>
        <button type="button" class="primary-button" @click="openCreate">＋ 新建场景</button>
      </div>

      <template v-if="activeTab === 'rules'">
      <div class="scene-config">
        <label>
          <span class="field-label">8级/11级默认识别字段</span>
          <select class="select">
            <option>level_7：建筑物/小区/自然村</option>
          </select>
        </label>
        <label>
          <span class="field-label">原始字段推荐识别字段</span>
          <select class="select">
            <option>poi：兴趣点</option>
            <option>subpoi：子兴趣点</option>
            <option>redundant：冗余描述</option>
            <option>others：其他字段</option>
          </select>
        </label>
        <p>8级和11级固定使用 level_7；原始字段自定义时可选择 poi、subpoi、redundant、others。</p>
      </div>

      <BaseTable :columns="sceneColumns" :rows="rules" row-key="id">
        <template #cell-statusText="{ row }">
          <span>{{ row.statusText }}</span>
        </template>
        <template #cell-actions="{ row }">
          <span class="link-group">
            <span class="action-link" @click="openEdit(row)">编辑</span>
            <span class="action-link danger" @click="removeScene(row.id)">删除</span>
          </span>
        </template>
      </BaseTable>

      <p class="scene-note">ⓘ 优先级越小，匹配优先级越高</p>
      <p v-if="feedbackMessage" class="success-note">{{ feedbackMessage }}</p>
      </template>

      <div v-else class="regex-test-panel">
        <div class="regex-test-header">
          <div>
            <h3>正则表达式在线测试</h3>
            <p>内嵌菜鸟工具正则测试页，可将场景规则复制到页面中进行匹配验证。</p>
          </div>
          <a class="secondary-button" href="https://www.jyshare.com/front-end/854/" target="_blank" rel="noreferrer">
            新窗口打开
          </a>
        </div>
        <div class="regex-test-frame-wrap">
          <iframe
            class="regex-test-frame"
            src="https://www.jyshare.com/front-end/854/"
            title="正则表达式在线测试"
            referrerpolicy="no-referrer"
          />
        </div>
        <p class="scene-note">如果第三方网站限制嵌入显示，请点击右上角“新窗口打开”。</p>
      </div>
    </section>

    <div v-if="showEditor" class="modal-mask" @click.self="showEditor = false">
      <div class="modal-card scene-modal">
        <div class="modal-body">
          <div class="modal-header">
            <div>
              <h3>{{ editingId ? '编辑场景' : '新建场景' }}</h3>
              <p>配置场景名称、正则表达式和用于匹配的字段。</p>
            </div>
            <button type="button" class="close-button" @click="showEditor = false">✕</button>
          </div>

          <div class="scene-form">
            <label>
              <span class="field-label">场景名称</span>
              <input v-model="form.name" class="input" placeholder="请输入场景名称" />
            </label>
            <label>
              <span class="field-label">优先级</span>
              <input v-model.number="form.priority" class="input" type="number" min="1" />
            </label>
            <label>
              <span class="field-label">8级/11级识别字段</span>
              <select class="select" disabled>
                <option value="level_7">level_7：建筑物/小区/自然村（必选）</option>
              </select>
            </label>
            <label>
              <span class="field-label">原始字段识别字段</span>
              <select v-model="form.rawMatchField" class="select">
                <option value="poi">poi：兴趣点</option>
                <option value="subpoi">subpoi：子兴趣点</option>
                <option value="redundant">redundant：冗余描述</option>
                <option value="others">others：其他字段</option>
              </select>
            </label>
            <label class="pattern-field">
              <span class="field-label">正则表达式</span>
              <textarea v-model="form.pattern" class="textarea" placeholder="请输入正则表达式" />
            </label>
          </div>

          <p v-if="errorMessage" class="error-note">{{ errorMessage }}</p>

          <div class="modal-footer">
            <button type="button" class="ghost-button" @click="showEditor = false">取消</button>
            <button type="button" class="primary-button" @click="saveScene">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createScene, deleteScene, getSceneList, resetDefaultScenes, updateScene } from '../api/address'
import BaseTable from '../components/BaseTable.vue'
import PageHeader from '../components/PageHeader.vue'
import TabSwitcher from '../components/TabSwitcher.vue'
import { sceneTabs } from '../mock/data'
import type { SceneRule, TableColumn } from '../types'

const activeTab = ref('rules')
const rules = ref<SceneRule[]>([])
const showEditor = ref(false)
const editingId = ref('')
const errorMessage = ref('')
const feedbackMessage = ref('')
const isResetting = ref(false)
const form = ref({
  name: '',
  pattern: '',
  rawMatchField: 'poi',
  priority: 1,
})

const sceneColumns: TableColumn[] = [
  { key: 'name', label: '场景名称', width: '130px' },
  { key: 'pattern', label: '识别规则（正则表达式）', width: '420px' },
  { key: 'matchField', label: '识别字段', width: '180px' },
  { key: 'priority', label: '优先级', width: '110px' },
  { key: 'statusText', label: '状态', width: '120px' },
  { key: 'actions', label: '操作', width: '140px' },
]

const loadScenes = async () => {
  rules.value = await getSceneList()
}

const rawMatchFieldOptions = ['poi', 'subpoi', 'redundant', 'others']

const getRawMatchField = (value: string) => {
  if (value.includes('/')) {
    const rawField = value.split('/')[1]?.trim()
    return rawMatchFieldOptions.includes(rawField) ? rawField : 'poi'
  }

  return rawMatchFieldOptions.includes(value) ? value : 'poi'
}

const buildMatchField = () => `level_7 / ${form.value.rawMatchField}`

const openCreate = () => {
  feedbackMessage.value = ''
  editingId.value = ''
  errorMessage.value = ''
  form.value = {
    name: '',
    pattern: '',
    rawMatchField: 'poi',
    priority: rules.value.length + 1,
  }
  showEditor.value = true
}

const openEdit = (rule: SceneRule) => {
  feedbackMessage.value = ''
  editingId.value = rule.id
  errorMessage.value = ''
  form.value = {
    name: rule.name,
    pattern: rule.pattern,
    rawMatchField: getRawMatchField(rule.matchField),
    priority: rule.priority,
  }
  showEditor.value = true
}

const saveScene = async () => {
  errorMessage.value = ''
  feedbackMessage.value = ''
  const payload = {
    name: form.value.name,
    pattern: form.value.pattern,
    matchField: buildMatchField(),
    priority: form.value.priority,
  }
  try {
    if (editingId.value) {
      await updateScene(editingId.value, payload)
    } else {
      await createScene(payload)
    }
    showEditor.value = false
    await loadScenes()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败'
  }
}

const removeScene = async (id: string) => {
  feedbackMessage.value = ''
  if (!window.confirm('确认删除这条场景规则吗？如果是系统默认规则，之后可通过“重置系统默认”补回。')) {
    return
  }
  try {
    await deleteScene(id)
    await loadScenes()
    feedbackMessage.value = '已删除场景规则'
  } catch (error) {
    feedbackMessage.value = ''
    errorMessage.value = error instanceof Error ? error.message : '删除失败'
  }
}

const resetDefaults = async () => {
  feedbackMessage.value = ''
  errorMessage.value = ''
  isResetting.value = true
  try {
    rules.value = await resetDefaultScenes()
    feedbackMessage.value = '已补回缺失的系统默认规则，现有已编辑规则保持不变'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置失败'
  } finally {
    isResetting.value = false
  }
}

onMounted(async () => {
  await loadScenes()
})
</script>

<style scoped>
.scene-toolbar {
  margin-bottom: 22px;
}

.scene-config {
  display: grid;
  grid-template-columns: 240px 240px 1fr;
  gap: 16px;
  align-items: end;
  margin-bottom: 22px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #f8fbff;
}

.scene-config label {
  display: grid;
  gap: 8px;
}

.scene-config p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.scene-note {
  margin: 18px 0 0;
  color: #64748b;
  font-size: 14px;
}

.regex-test-panel {
  display: grid;
  gap: 16px;
}

.regex-test-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #f8fbff;
}

.regex-test-header h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.regex-test-header p {
  margin: 0;
  color: #64748b;
}

.regex-test-frame-wrap {
  width: 100%;
  min-height: 720px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: #fff;
}

.regex-test-frame {
  width: 100%;
  min-height: 820px;
  margin-top: -86px;
  border: 0;
  background: #fff;
}

.scene-modal {
  width: min(760px, 100%);
}

.scene-form {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 16px;
  margin: 20px 0;
}

.scene-form label {
  display: grid;
  gap: 8px;
}

.pattern-field {
  grid-column: 1 / -1;
}

.pattern-field .textarea {
  min-height: 140px;
}

.error-note {
  color: var(--danger);
  font-weight: 600;
}

.success-note {
  margin: 12px 0 0;
  color: #0f766e;
  font-weight: 700;
}
</style>
