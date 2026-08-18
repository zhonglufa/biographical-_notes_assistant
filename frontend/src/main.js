// 应用入口（Vue 3 栈，遵守 ADR-010：Vue 3 + Element Plus）。
import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import App from './App.vue';
import router from './router.js';
import './styles/tokens.css'; // 设计 token + Element Plus 主题对齐（须在 element-plus css 之后导入以覆盖）

createApp(App).use(router).use(ElementPlus).mount('#app');
