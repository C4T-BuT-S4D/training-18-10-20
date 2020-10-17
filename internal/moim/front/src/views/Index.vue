<template>
    <layout>
        <div class="ui text container">
            <h1 class="ui header">Welcome to the moim!</h1>
            <div class="ui one column grid">
                <div class="column">
                    <h3>The best service to organize anime syncs</h3>
                    <img class="ui image" :src="`${publicPath}anime.jpg`">
                </div>
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
                publicPath: process.env.BASE_URL
            }
        }
    };
</script>