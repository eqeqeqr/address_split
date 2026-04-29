<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-mark" />
      <span>地址拆分工具</span>
    </div>

    <nav class="nav-list">
      <component
        :is="item.path ? 'RouterLink' : 'div'"
        v-for="item in navigationItems"
        :key="item.label"
        :to="item.path"
        class="nav-item"
        :class="{ active: item.path && route.path.startsWith(item.path), mutedItem: !item.path }"
      >
        <span class="nav-icon" :data-icon="item.icon" />
        <span>{{ item.label }}</span>
      </component>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { navigationItems } from '../mock/data'

const route = useRoute()
</script>

<style scoped>
.sidebar {
  width: 236px;
  padding: 26px 18px;
  border-right: 1px solid var(--border);
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #101828;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 30px;
}

.brand-mark {
  width: 26px;
  height: 26px;
  background: linear-gradient(180deg, #2285ff 0%, #1868ff 100%);
  border-radius: 50% 50% 50% 10%;
  position: relative;
}

.brand-mark::after {
  content: "";
  position: absolute;
  left: 8px;
  top: 8px;
  width: 10px;
  height: 10px;
  background: #fff;
  border-radius: 50%;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 56px;
  padding: 0 18px;
  border-radius: 14px;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.nav-item.active {
  color: var(--primary);
  background: #edf4ff;
}

.nav-item.mutedItem {
  cursor: default;
}

.nav-icon {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  border: 2px solid currentColor;
  position: relative;
  flex: none;
}

.nav-icon[data-icon='home'] {
  transform: rotate(45deg) scale(0.85);
  border-radius: 4px;
}

.nav-icon[data-icon='home']::after {
  content: "";
  position: absolute;
  inset: 6px;
  background: currentColor;
  transform: rotate(-45deg);
}

.nav-icon[data-icon='scene']::before,
.nav-icon[data-icon='scene']::after,
.nav-icon[data-icon='record']::before,
.nav-icon[data-icon='help']::before,
.nav-icon[data-icon='config']::before,
.nav-icon[data-icon='config']::after {
  content: "";
  position: absolute;
}

.nav-icon[data-icon='scene']::before {
  left: 3px;
  top: 3px;
  width: 6px;
  height: 12px;
  border: 2px solid currentColor;
  border-radius: 6px;
}

.nav-icon[data-icon='scene']::after {
  right: 3px;
  top: 3px;
  width: 6px;
  height: 12px;
  border: 2px solid currentColor;
  border-radius: 6px;
}

.nav-icon[data-icon='record']::before {
  inset: 4px;
  border: 2px solid currentColor;
  border-radius: 4px;
}

.nav-icon[data-icon='help'] {
  border-radius: 50%;
}

.nav-icon[data-icon='help']::before {
  left: 8px;
  top: 3px;
  color: currentColor;
  content: "?";
  font-weight: 700;
}

.nav-icon[data-icon='config'] {
  border-radius: 50%;
}

.nav-icon[data-icon='config']::before {
  inset: 5px;
  border: 2px solid currentColor;
  border-radius: 50%;
}

.nav-icon[data-icon='config']::after {
  left: 9px;
  top: -5px;
  width: 2px;
  height: 30px;
  background: currentColor;
  transform: rotate(45deg);
}
</style>
