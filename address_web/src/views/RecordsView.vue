<template>
  <div>
    <PageHeader title="拆分记录" subtitle="查看历史拆分任务记录，可重新下载结果" />

    <section class="card section-card">
      <div class="toolbar records-filters">
        <div class="filter-item">
          <span class="field-label">任务名称</span>
          <input v-model="taskKeyword" class="input" placeholder="请输入任务名称" />
        </div>
        <div class="filter-item">
          <span class="field-label">状态</span>
          <select v-model="statusFilter" class="select">
            <option v-for="item in statusOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </div>
        <div class="filter-item">
          <span class="field-label">时间</span>
          <div class="date-field">
            <span>选择日期范围</span>
            <span>🗓</span>
          </div>
        </div>
        <button type="button" class="ghost-button" @click="resetFilters">重置</button>
      </div>

      <BaseTable :columns="recordColumns" :rows="filteredRecords" row-key="id">
        <template #cell-total="{ row }">{{ formatNumber(row.total) }}</template>
        <template #cell-success="{ row }">{{ formatNumber(row.success) }}</template>
        <template #cell-failed="{ row }">{{ formatNumber(row.failed) }}</template>
        <template #cell-status="{ row }">
          <StatusBadge
            :text="row.status === 'success' ? '完成' : '部分失败'"
            :tone="row.status === 'success' ? 'success' : 'warning'"
          />
        </template>
        <template #cell-actions="{ row }">
          <span class="link-group">
            <RouterLink class="action-link" :to="`/records/${row.id}`">查看</RouterLink>
            <a class="action-link" :href="row.downloadUrl" target="_blank" rel="noreferrer">下载</a>
            <span class="action-link danger" @click="removeRecord(row.id)">删除</span>
          </span>
        </template>
      </BaseTable>

      <PaginationBar
        total-text="25 条"
        page-size-text="10条/页"
        :pages="[1, 2, 3]"
        :active-page="1"
        :tail-page="3"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { deleteSplitRecord, getSplitRecords } from '../api/address'
import BaseTable from '../components/BaseTable.vue'
import PageHeader from '../components/PageHeader.vue'
import PaginationBar from '../components/PaginationBar.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { statusOptions } from '../mock/data'
import type { SplitRecord, TableColumn } from '../types'

const records = ref<SplitRecord[]>([])
const taskKeyword = ref('')
const statusFilter = ref('all')

const recordColumns: TableColumn[] = [
  { key: 'taskName', label: '任务名称', width: '250px' },
  { key: 'source', label: '数据来源', width: '120px' },
  { key: 'total', label: '总条数', width: '110px' },
  { key: 'success', label: '成功条数', width: '120px' },
  { key: 'failed', label: '失败条数', width: '120px' },
  { key: 'status', label: '状态', width: '110px' },
  { key: 'startedAt', label: '开始时间', width: '180px' },
  { key: 'actions', label: '操作', width: '150px' },
]

const filteredRecords = computed(() =>
  records.value.filter((item) => {
    const byKeyword = !taskKeyword.value || item.taskName.includes(taskKeyword.value)
    const byStatus = statusFilter.value === 'all' || item.status === statusFilter.value
    return byKeyword && byStatus
  }),
)

const resetFilters = () => {
  taskKeyword.value = ''
  statusFilter.value = 'all'
}

const loadRecords = async () => {
  records.value = await getSplitRecords()
}

const removeRecord = async (id: string) => {
  await deleteSplitRecord(id)
  await loadRecords()
}

const formatNumber = (value: number) => new Intl.NumberFormat('zh-CN').format(value)

onMounted(async () => {
  await loadRecords()
})
</script>

<style scoped>
.records-filters {
  align-items: flex-end;
  margin-bottom: 22px;
}

.filter-item {
  display: grid;
  gap: 8px;
}

.filter-item:nth-child(1) {
  width: 290px;
}

.filter-item:nth-child(2) {
  width: 190px;
}

.filter-item:nth-child(3) {
  width: 240px;
}
</style>
