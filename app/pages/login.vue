<script setup lang="ts">
definePageMeta({ layout: false });
const { user } = useSession();
const username = ref("admin"),
  password = ref(""),
  busy = ref(false),
  error = ref("");
async function login() {
  busy.value = true;
  error.value = "";
  try {
    user.value = (await $fetch("/api/auth/login", {
      method: "POST",
      body: { username: username.value, password: password.value },
    })) as any;
    await navigateTo("/");
  } catch (e: any) {
    error.value = e.data?.statusMessage || "登录失败，请稍后重试";
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <main class="login-page">
    <div class="login-brand">
      <span class="brand-icon"><AppIcon name="Boxes" :size="23" /></span>
      Registry Manager
    </div>
    <section class="login-card">
      <h1>登录</h1>
      <p class="muted">使用 Registry Manager 账号登录。</p>
      <form @submit.prevent="login">
        <label
          >用户名<input
            v-model="username"
            autocomplete="username"
            required
            placeholder="admin" /></label
        ><label
          >密码<input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            placeholder="输入登录密码"
        /></label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="btn primary" :disabled="busy">
          {{ busy ? "正在登录…" : "登录" }}<AppIcon name="ArrowRight" />
        </button>
      </form>
      <div class="login-foot">
        <AppIcon name="ShieldCheck" :size="15" /> 凭证通过安全会话保存于服务端
      </div>
    </section>
    <div class="login-bottom">Registry Manager</div>
  </main>
</template>
