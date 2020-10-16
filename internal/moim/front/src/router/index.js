import Vue from 'vue';
import VueRouter from 'vue-router';
import Index from '@/views/Index';
import Register from "@/views/Register";
import Login from "@/views/Login";
import Home from "@/views/Home";
import Feed from "@/views/Feed";
import Members from "@/views/Members";
import Join from "@/views/Join";
import Details from "@/views/Details";
import Create from "@/views/Create";

Vue.use(VueRouter);

const routes = [
    {
        path: '/',
        name: 'Index',
        component: Index
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
    },
    {
        path: '/login',
        name: 'Login',
        component: Login,
    },
    {
      path: '/create',
      name: 'Create',
      component: Create,
    },
    {
        path: '/home',
        name: 'Home',
        component: Home,
    },
    {
        path: '/feed',
        name: 'Feed',
        component: Feed,
    },
    {
        path: '/members/:syncId/:syncName',
        name: 'Members',
        component: Members,
    },
    {
        path: '/join/:syncId',
        name: 'Join',
        component: Join,
    },
    {
        path: '/ticket/:publicId',
        name: 'Details',
        component: Details,
    }
];

const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes
});

export default router;
