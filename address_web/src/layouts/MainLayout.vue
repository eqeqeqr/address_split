<template>
  <div class="page-shell">
    <div class="app-frame">
      <AppSidebar />
      <main class="content-panel">
        <header class="topbar">
          <div class="user-entry">
            <span class="user-icon" />
            <span>管理员</span>
            <span class="muted">⌄</span>
          </div>
        </header>
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'
</script>
