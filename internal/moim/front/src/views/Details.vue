<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>You joined sync: <b>"{{ title }}"</b> as <b>"{{ nickname }}"</b></p>
            <p>Description of the sync: {{ description }}</p>
            <p v-if="ticket_url != null">Your ticket available at <a :href="ticket_url">{{ ticket_url }}</a></p>
            <p v-else>Your ticket will be available soon. Please refresh page in 30s</p>
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
        computed: {
            title: function () {
                console.log('title', this.sync);
                if (this.sync) {
                    return this.sync.title;
                }
                return '';
            },
            description: function () {
                console.log('desc', this.sync);
                if (this.sync) {
                    return this.sync.description;
                }
                return '';
            }
        },
        async mounted() {
            this.publicId = this.$route.params.publicId;
            console.log(this.ticket_url);
            await this.getTicket();
        },
        methods: {
            async getTicket() {
                try {
                    let res = await this.$http.get(`ticket/${this.publicId}`);
                    this.sync = res.data.sync;
                    this.nickname = res.data.nickname;
                    console.log(res.data.ticket_url);
                    if (res.data.ticket_url !== undefined) {
                        this.ticket_url = res.data.ticket_url;
                    }
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