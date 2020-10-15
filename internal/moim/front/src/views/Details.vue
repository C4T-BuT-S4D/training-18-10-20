<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>You joined sync: <b>"{{ sync !== undefined ? sync.title : "" }}"</b> as <b>"{{ nickname }}"</b></p>
            <p>Description of the sync: {{sync !== undefined ?  sync.description : "" }}</p>
            <p>Your ticket available at <a :href="ticket_url">{{ ticket_url }}</a></p>
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
                sync: null,
                nickname: null,
                ticket_url: null,
                publicId: null,
                errorVisible: false,
                error: null,
            }
        },
        async mounted() {
            this.publicId = this.$route.params.publicId;
            await this.getTicket();
        },
        methods: {
            async getTicket() {
                try {
                    let res = await this.$http.get(`ticket/${this.publicId}`);
                    this.sync = res.data.sync;
                    this.nickname = res.data.nickname;
                    this.ticket_url = res.data.ticket_url;
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