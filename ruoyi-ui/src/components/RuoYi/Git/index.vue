<template>
  <div>
    <svg-icon icon-class="github" @click="goto" />
  </div>
</template>

<script>
export default {
  name: 'RuoyiCRMGit',
  data() {
    return {
      url: 'https://gitee.com/jundee/RuoyiCRM',
    }
  },
  methods: {
    goto() {
      window.open(this.url)
    },
  },
}
</script>