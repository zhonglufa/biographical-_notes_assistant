// 路由表（Vue Router 4，hash 模式，与 React 版 #/applications 等对齐）。
// 未登录守卫在 App.vue 内（无 token 仅渲染 Auth，不暴露业务数据，PRD §797）。
import { createRouter, createWebHashHistory } from 'vue-router';
import Applications from './screens/Applications.vue';
import Resume from './screens/Resume.vue';
import Jobs from './screens/Jobs.vue';
import Notifications from './screens/Notifications.vue';
import DailyReport from './screens/DailyReport.vue';
import Strategy from './screens/Strategy.vue';
import Account from './screens/Account.vue';
import Adapter from './screens/Adapter.vue';
import Interview from './screens/Interview.vue';
import Payment from './screens/Payment.vue';

const routes = [
  { path: '/', redirect: '/applications' },
  { path: '/applications', name: 'applications', component: Applications },
  { path: '/resume', name: 'resume', component: Resume },
  { path: '/jobs', name: 'jobs', component: Jobs },
  { path: '/strategy', name: 'strategy', component: Strategy },
  { path: '/adapters', name: 'adapters', component: Adapter },
  { path: '/interview', name: 'interview', component: Interview },
  { path: '/membership', name: 'membership', component: Payment },
  { path: '/notifications', name: 'notifications', component: Notifications },
  { path: '/daily', name: 'daily', component: DailyReport },
  { path: '/account', name: 'account', component: Account },
  { path: '/:pathMatch(.*)*', redirect: '/applications' },
];

export default createRouter({
  history: createWebHashHistory(),
  routes,
});
