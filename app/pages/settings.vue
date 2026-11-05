<script setup lang="ts">
const { settings, health, host, password, changePassword, passwordBusy } =
  useWorkspace();
</script>
<template>
  <section class="panel settings-panel">
    <div class="panel-title">
      <div>
        <h2>Registry 连接</h2>
        <p>连接配置由部署环境变量管理</p>
      </div>
      <span class="badge" :class="{ public: health?.connected }">{{
        health?.connected ? "已连接" : "未连接"
      }}</span>
    </div>
    <dl>
      <div>
        <dt>上游地址</dt>
        <dd class="mono">{{ settings?.registry_url || "—" }}</dd>
      </div>
      <div>
        <dt>客户端地址</dt>
        <dd class="mono">{{ host }}</dd>
      </div>
      <div>
        <dt>镜像删除</dt>
        <dd>{{ settings?.allow_tag_delete ? "已启用" : "未启用" }}</dd>
      </div>
      <div>
        <dt>存储方式</dt>
        <dd>SQLite · 兼容原有数据库</dd>
      </div>
    </dl>
    <div class="inline-note">
      <AppIcon name="CircleHelp" :size="17" />修改连接地址后需重新启动服务。删除
      Manifest 后，仍需单独执行 Registry 垃圾回收以释放磁盘。
    </div>
  </section>
  <section class="panel settings-panel">
    <div class="panel-title">
      <div>
        <h2>账户安全</h2>
        <p>修改密码后，所有浏览器会话将失效，需要重新登录。</p>
      </div>
      <AppIcon name="ShieldCheck" />
    </div>
    <form class="password-form" @submit.prevent="changePassword">
      <label
        >当前密码<input
          v-model="password.current_password"
          type="password"
          autocomplete="current-password"
          required /></label
      ><label
        >新密码<input
          v-model="password.new_password"
          type="password"
          autocomplete="new-password"
          minlength="8"
          required
          placeholder="至少 8 个字符" /></label
      ><button class="btn primary" :disabled="passwordBusy">
        {{ passwordBusy ? "正在保存…" : "更新密码" }}
      </button>
    </form>
  </section>
</template>
