<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <p>Members of sync <b>"{{ syncName }}"</b></p>
            <div class="ui info message" v-for="(member) in members" :key="member.id">
                <p>{{ member.nickname }}</p>
                <p><a :href="`/tickets/${member.public_id}.pdf`">Ticket</a></p>
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
                members: [],
                syncName: null,
                error: null,
                errorVisible: false,
            }
        },
        async mounted() {
            await this.getMembers();
        },
        methods: {
            async getMembers() {
                try {
                    let syncId = this.$route.params.syncId;
                    this.syncName = this.$route.params.syncName;
                    let res = await this.$http.get('sync/' + syncId.toString());
                    this.members = res.data;
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