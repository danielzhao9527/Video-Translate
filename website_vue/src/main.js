import { createApp } from 'vue';
import App from './App.vue';
import axios from 'axios';

import 'video.js/dist/video-js.css';
// import './assets/styles4.css';
import ElementPlus from 'element-plus'; // 引入 Element Plus
import 'element-plus/theme-chalk/el-button.css'; // 引入具体组件的样式
import 'element-plus/theme-chalk/index.css'; // 引入 Element Plus 的样式

axios.defaults.baseURL = 'http://localhost:8000';

const app = createApp(App);
app.use(ElementPlus); // 注册 Element Plus
app.mount('#app');
