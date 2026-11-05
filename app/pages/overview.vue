<script setup lang="ts">
const { overview, date, pageBusy } = useWorkspace();
</script>
<template>
  <WorkspaceMetrics />
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>最近推拉活动</h2>
        <p>仅统计经过本服务 /v2 入口的成功 Manifest 请求</p>
      </div>
      <span class="badge public"
        >近 30 天推送 {{ overview?.pushes_30d ?? "—" }}</span
      >
    </div>
    <div
      v-if="!pageBusy && !overview?.recent_events?.length"
      class="empty-state"
    >
      <AppIcon name="Activity" :size="30" />
      <h3>还没有推拉记录</h3>
      <p>通过本服务的 Registry 地址推拉后，活动会显示在这里。</p>
    </div>
    <div
      v-for="event in overview?.recent_events"
      :key="event.id"
      class="event-row"
    >
      <span class="repo-icon teal"
        ><AppIcon
          :name="event.action === 'pull' ? 'ArrowDownToLine' : 'ArrowUpRight'"
      /></span>
      <div>
        <b>{{ event.repository }}</b
        ><small>{{ event.tag }}</small>
      </div>
      <span class="badge">{{ event.action === "pull" ? "拉取" : "推送" }}</span
      ><time>{{ date(event.created_at) }}</time>
    </div>
  </section>
</template>
