<script setup lang="ts">
const { repos, repoError, totalTags, overview } = useWorkspace();
</script>
<template>
  <dl class="summary-line">
    <div>
      <dt>仓库</dt>
      <dd>{{ repoError ? "—" : repos.length }}</dd>
    </div>
    <div>
      <dt>标签</dt>
      <dd>{{ repoError ? "—" : totalTags }}</dd>
    </div>
    <div>
      <dt>近 30 天拉取</dt>
      <dd>{{ overview?.pulls_30d ?? "—" }}</dd>
    </div>
    <div>
      <dt>近 30 天推送</dt>
      <dd>{{ overview?.pushes_30d ?? "—" }}</dd>
    </div>
  </dl>
</template>
