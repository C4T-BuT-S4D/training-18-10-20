<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>Welcome home, {{ this.$store.state.user }}</p>
            <p><router-link :to="{name: 'Create'}">Create sync
            </router-link></p>
            <p>Your organized syncs:</p>
            <div class="ui info message" v-for="(sync) in syncs" :key="sync.id">
                <p>Id: {{ sync.id }}</p>
                <p>Title: {{ sync.title }}</p>
                <p>Description: {{ sync.description }}</p>
                <p>Capacity left: {{ sync.capacity }}</p>
                <router-link :to="{name: 'Members', params: {syncId: sync.id, syncName: sync.title}}">See the members
                </router-link>
            </div>
        </div>

        <br>
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
                errorVisible: false,
            }
        },
        async mounted() {
            await this.getUserPosts();
        },
        methods: {
            async getUserPosts() {
                try {
                    let res = await this.$http.get('sync');
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