<template>
  <div class="dashboard-editor-container">

    <panel-group :customer-data="customerData" />

    <el-row :gutter="10">
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card class="box-card">
          <div slot="header" class="clearfix">
            <span>今日待办</span>
          </div>
          <table class="followup-table">
            <tbody>
              <tr>
                <th>今日已跟进</th>
                <td>{{followupData.today_followup}}</td>
              </tr>
              <tr>
                <th>未跟进个数</th>
                <td>{{followupData.no_followup}}</td>
              </tr>
              <tr>
                <th>跟进率</th>
                <td>{{followupData.followup_rate}} %</td>
              </tr>
            </tbody>
          </table>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card class="box-card">
          <div slot="header" class="clearfix">
            <span>今日跟进提醒</span>
          </div>
          <div class="today-followup" v-for="followup in todayFollowupList" :key="followup">
            <span style="color:red;">跟进</span> <a class="followup-customer" href="#">{{followup.name}}</a><br>
            <span class="time">下次跟进时间：{{parseTime(followup.nextFollowupTime)}}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card class="box-card">
          <div slot="header" class="clearfix">
            <span>动态</span>
          </div>
          <div class="today-updates" v-for="updates in todayUpdates" :key="updates">
            {{updates.owner}} <span style="color:red;">跟进</span> <a class="updates-customer" href="#">{{updates.customerName}}</a><br>
            <span class="content">跟进记录：</span>{{updates.content}}<br>
            <span class="time">跟进时间：{{parseTime(updates.createTime)}}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import PanelGroup from './dashboard/PanelGroup'

import { indexData } from '@/api/crm/index'


export default {
  name: 'Index',
  components: {
    PanelGroup
  },
  data () {
    return {
      customerData: {},
      followupData: {},
      todayFollowupList: [],
      todayUpdates: []
    }
  },
  created () {
    this.initData();
  },
  methods: {
    initData () {
      indexData().then((response) => {
        this.customerData = response.data.customer_info;
        this.followupData = response.data.followup_info;
        this.todayFollowupList = response.data.today_followup_list;
        this.todayUpdates = response.data.today_updates;
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-editor-container {
  padding: 32px;
  // background-color: rgb(240, 242, 245);
  position: relative;

  .chart-wrapper {
    background: #fff;
    padding: 16px 16px 0;
    margin-bottom: 32px;
  }
}
.followup-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #eee;
}
.followup-table th {
  width: 150px;
}
.followup-table th,
td {
  color: #7e7e7e;
  border: 1px solid #eee;
  text-align: left;
  padding: 10px;
}

.today-updates {
  font-size: 14px;
  padding: 18px 0;
  border-bottom: 1px solid #eee;
}

.today-updates .updates-customer {
  color: blue;
}
.today-updates .content {
  color: #ee8323;
}

.today-followup {
  font-size: 14px;
  padding: 18px 0;
  border-bottom: 1px solid #eee;
}

.time {
  color: #7e7e7e;
}

@media (max-width: 1024px) {
  .chart-wrapper {
    padding: 8px;
  }
}
</style>
