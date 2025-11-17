import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const loginVisible = ref(false)
  const showLogin = () => { loginVisible.value = true }
  const hideLogin = () => { loginVisible.value = false }
  return { loginVisible, showLogin, hideLogin }
})