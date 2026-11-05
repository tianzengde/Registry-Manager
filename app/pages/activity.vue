<script setup lang="ts">
const { logs, activitySearch, logPage, loadPage, pageBusy, date } =
  useWorkspace();
</script>
<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <h2>操作审计</h2>
        <p>登录、密码、仓库权限与镜像删除记录</p>
      </div>
      <form
        class="search-field"
        @submit.prevent="
          logPage = 0;
          loadPage();
        "
      >
        <AppIcon name="Search" :size="16" /><input
          v-model="activitySearch"
          placeholder="搜索后按回车"
          aria-label="搜索操作记录"
        />
      </form>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>操作</th>
            <th>目标 / 说明</th>
            <th>操作人</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in logs.items" :key="item.id">
            <td>
              <span class="badge">{{
                (
                  {
                    login: "登录",
                    delete: "删除镜像",
                    password: "修改密码",
                    "repo.update_visibility": "修改权限",
                  } as any
                )[item.action] || item.action
              }}</span>
            </td>
            <td>
              <b>{{ item.target }}</b
              ><small class="cell-detail">{{ item.detail }}</small>
            </td>
            <td>{{ item.actor }}</td>
            <td class="mono muted">{{ date(item.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!pageBusy && !logs.items.length" class="empty-state">
      <AppIcon name="Activity" :size="28" />
      <h3>暂无操作记录</h3>
    </div>
    <div class="table-footer">
      <span>共 {{ logs.total }} 条记录</span>
      <div class="pagination">
        <button
          class="btn"
          :disabled="!logPage || pageBusy"
          @click="
            logPage--;
            loadPage();
          "
        >
          上一页</button
        ><span>{{ logPage + 1 }}</span
        ><button
          class="btn"
          :disabled="(logPage + 1) * 30 >= logs.total || pageBusy"
          @click="
            logPage++;
            loadPage();
          "
        >
          下一页
        </button>
      </div>
    </div>
  </section>
</template>
