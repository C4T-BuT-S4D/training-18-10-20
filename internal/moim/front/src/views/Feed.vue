<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>Sync feed</p>
            <div class="ui info message" v-for="(sync) in syncs" :key="sync.id">
                <p>Id: {{ sync.id }}</p>
                <p>Title: {{ sync.title }}</p>
                <p>Description: {{ sync.description }}</p>
                <p>Capacity left: {{ sync.capacity }}</p>
                <router-link :to="{name: 'Join', params: {syncId: sync.id}}">Join
                </router-link>
            </div>
        </div>
    </layout>
</template>
<script>
    import Layout from './Layout';

    export default {
        components: {
            Layout
        },
        data() {
            return {
                syncs: [],
                error: null,
                errorVisible: false,
            }
        },
        async mounted() {
            await this.getSyncs();
        },
        methods: {
            async getSyncs() {
                try {
                    let res = await this.$http.get('syncs');
                    this.syncs = res.data;
                } catch (error) {
                    this.error = error.response.data.error;
                    this.errorVisible = true;
                }
            },
            handleDismiss() {
                this.errorVisible = false;
            },
        }
    };
</script>