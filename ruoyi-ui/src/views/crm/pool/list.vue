<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="日期查询" prop="createTime">
        <el-date-picker clearable size="small" v-model="queryParams.createTime" type="date" value-format="yyyy-MM-dd" placeholder="选择日期">
        </el-date-picker>
      </el-form-item>
      <el-form-item label="客户名称" prop="name">
        <el-input v-model="queryParams.name" placeholder="请输入客户名称" clearable size="small" @keyup.enter.native="handleQuery" />
      </el-form-item>
      <el-form-item label="联系电话" prop="phone">
        <el-input v-model="queryParams.phone" placeholder="请输入联系电话" clearable size="small" @keyup.enter.native="handleQuery" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="customerList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="客户名称" align="left" prop="name" />
      <el-table-column label="客户级别" align="left" prop="customerRank">
        <template slot-scope="scope">
          <dict-tag :options="dict.type.customer_rank" :value="scope.row.customerRank" />
        </template>
      </el-table-column>
      <el-table-column label="最后跟进记录" align="center" prop="lastUpdateRecord" />
      <el-table-column label="最后跟进时间" align="center" prop="lastFollowupTime" width="180">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.lastFollowupTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="转公海时间" align="center" prop="toPoolTime" width="180">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.toPoolTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="前负责人" align="center" prop="preManager" />
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button size="mini" type="text" icon="el-icon-finished" @click="handleReceive(scope.row)" v-hasPermi="['crm:pool:receive']">领取</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" :page.sync="queryParams.pageNum" :limit.sync="queryParams.pageSize" @pagination="getList" />
  </div>
</template>

<script>
import { listCustomer, receiveCustomer } from '@/api/crm/pool'

export default {
  name: 'Pool',
  dicts: [
    'clues_source',
    'customer_industry',
    'clues_status',
    'customer_rank',
    'region_list',
    'customer_status',
  ],
  data () {
    return {
      // 遮罩层
      loading: true,
      // 选中数组
      ids: [],
      // 非单个禁用
      single: true,
      // 非多个禁用
      multiple: true,
      // 显示搜索条件
      showSearch: true,
      // 总条数
      total: 0,
      // 客户表格数据
      customerList: [],
      // 弹出层标题
      title: '',
      // 是否显示弹出层
      open: false,
      // 查询参数
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        code: null,
        name: null,
        linkman: null,
        phone: null,
        region: null,
        customerIndustry: null,
        customerRank: null,
        customerStatus: null,
        cluesName: null,
        cluesSource: null,
        cluesStatus: null,
        manager: null,
      },
      // 表单参数
      form: {},
      // 表单校验
      rules: {},
    }
  },
  created () {
    this.getList()
  },
  methods: {
    /** 查询客户列表 */
    getList () {
      this.loading = true
      listCustomer(this.queryParams).then((response) => {
        this.customerList = response.rows
        this.total = response.total
        this.loading = false
      })
    },

    /** 搜索按钮操作 */
    handleQuery () {
      this.queryParams.pageNum = 1
      this.getList()
    },
    /** 重置按钮操作 */
    resetQuery () {
      this.resetForm('queryForm')
      this.handleQuery()
    },
    // 多选框选中数据
    handleSelectionChange (selection) {
      this.ids = selection.map((item) => item.id)
      this.single = selection.length !== 1
      this.multiple = !selection.length
    },

    /** 导出按钮操作 */
    handleExport () {
      this.download(
        'crm/pool/export',
        {
          ...this.queryParams,
        },
        `客户公海_${new Date().getTime()}.xlsx`
      )
    },
    handleReceive (row) {
      const id = row.id;
      receiveCustomer(id).then((response) => {
        this.$modal.msgSuccess('领取成功')
        this.getList()
      })
    }
  },
}
</script>
