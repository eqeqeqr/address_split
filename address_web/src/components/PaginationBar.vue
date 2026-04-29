<template>
  <div class="pagination">
    <div class="toolbar">
      <span class="field-label">共 {{ totalText }}</span>
      <select class="select" style="width: 120px">
        <option>{{ pageSizeText }}</option>
      </select>
    </div>

    <div class="pagination-controls">
      <button type="button" class="page-arrow">〈</button>
      <button
        v-for="page in pages"
        :key="page"
        type="button"
        class="page-chip"
        :class="{ active: page === activePage }"
        @click="$emit('change', page)"
      >
        {{ page }}
      </button>
      <span v-if="tailPage > pages.length" class="muted">...</span>
      <button v-if="tailPage > pages.length" type="button" class="page-chip" @click="$emit('change', tailPage)">
        {{ tailPage }}
      </button>
      <button type="button" class="page-arrow" @click="$emit('change', activePage + 1)">〉</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  totalText: string
  pageSizeText: string
  pages: number[]
  activePage: number
  tailPage: number
}>()

defineEmits<{
  (event: 'change', page: number): void
}>()
</script>
