<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>Join sync <b>"{{ syncName }}"</b> by <b>"{{ author_email }}"</b></p>
            <p>About: {{ syncDescription}}</p>
            <p>Capacity: {{ capacity }}</p>
            <form class="ui form" @submit="join" method="post" action="">
                <div class="field">
                    <label>Nickname</label>
                    <input type="text" required name="nickname" v-model="nickName" placeholder="Jojo">
                </div>
                <button class="ui button" type="submit" :disabled="!!isLoading">Join</button>
            </form>
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
                nickName: null,
                sync: null,
                syncId: null,
                syncName: null,
                syncDescription: null,
                capacity: null,
                author_email: null,
                error: null,
                errorVisible: false,
                isLoading: false,
            }
        },
        async mounted() {
            this.syncId = this.$route.params.syncId;
            this.loadTicket();
        },
        methods: {
            handleDismiss() {
                this.errorVisible = false;
            },
            async loadTicket() {
                try {
                    let res = await this.$http.get(`sync/${this.syncId}/info`);
                    this.syncName = res.data.title;
                    this.syncDescription = res.data.description;
                    this.capacity = res.data.capacity;
                    this.author_email = res.data.author.email;
                } catch (error) {
                    this.error = error.response.data.error;
                    this.errorVisible = true;
                }
            },
            async join(event) {
                try {
                    event.preventDefault();
                    this.isLoading = true;
                    let res = await this.$http.post(`sync/${this.syncId}/join`, {
                        nickname: this.nickName,
                    });
                    this.isLoading = false;
                    this.$router.push({name: 'Details', params: {publicId: res.data.public_id}}).catch(() => {
                    });
                } catch (error) {
                    this.isLoading = false;
                    this.error = error.response.data.error;
                    this.errorVisible = true;
                }
            },
        }
    };
</script>