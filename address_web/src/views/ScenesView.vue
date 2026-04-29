<template>
  <div>
    <PageHeader
      title="自定义场景"
      subtitle="管理地址中的场景规则(识别规则，系统默认规则不可删除，可新增或编辑自定义规则)"
    />

    <section class="card section-card">
      <div class="toolbar scene-toolbar">
        <TabSwitcher v-model="activeTab" :tabs="sceneTabs" compact />
        <div class="toolbar-spacer" />
        <button type="button" class="primary-button" @click="openCreate">＋ 新建场景</button>
      </div>

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
          </select>
        </label>
        <p>用户选择原始字段自定义时，需要在拆分页明确选择用于场景正则匹配的字段。</p>
      </div>

      <BaseTable :columns="sceneColumns" :rows="rules" row-key="id">
        <template #cell-statusText="{ row }">
          <span>{{ row.statusText }}</span>
        </template>
        <template #cell-actions="{ row }">
          <span v-if="!row.editable">-</span>
          <span v-else class="link-group">
            <span class="action-link" @click="openEdit(row)">编辑</span>
            <span class="action-link danger" @click="removeScene(row.id)">删除</span>
          </span>
        </template>
      </BaseTable>

      <p class="scene-note">ⓘ 优先级越小，匹配优先级越高</p>
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
              <span class="field-label">识别字段</span>
              <input v-model="form.matchField" class="input" placeholder="level_7 / poi" />
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
import { createScene, deleteScene, getSceneList, updateScene } from '../api/address'
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
const form = ref({
  name: '',
  pattern: '',
  matchField: 'level_7 / poi',
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

const openCreate = () => {
  editingId.value = ''
  errorMessage.value = ''
  form.value = {
    name: '',
    pattern: '',
    matchField: 'level_7 / poi',
    priority: rules.value.length + 1,
  }
  showEditor.value = true
}

const openEdit = (rule: SceneRule) => {
  editingId.value = rule.id
  errorMessage.value = ''
  form.value = {
    name: rule.name,
    pattern: rule.pattern,
    matchField: rule.matchField,
    priority: rule.priority,
  }
  showEditor.value = true
}

const saveScene = async () => {
  errorMessage.value = ''
  try {
    if (editingId.value) {
      await updateScene(editingId.value, form.value)
    } else {
      await createScene(form.value)
    }
    showEditor.value = false
    await loadScenes()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败'
  }
}

const removeScene = async (id: string) => {
  await deleteScene(id)
  await loadScenes()
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

.scene-modal {
  width: min(760px, 100%);
}

.scene-form {
  display: grid;
  grid-template-columns: 1fr 140px;
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
</style>
