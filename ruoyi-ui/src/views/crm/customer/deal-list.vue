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
      <el-form-item label="客户级别" prop="customerRank">
        <el-select v-model="queryParams.customerRank" placeholder="请选择客户级别" clearable size="small">
          <el-option v-for="dict in dict.type.customer_rank" :key="dict.value" :label="dict.label" :value="dict.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="客户状态" prop="customerStatus">
        <el-select v-model="queryParams.customerStatus" placeholder="请选择客户状态" clearable size="small">
          <el-option v-for="dict in dict.type.customer_status" :key="dict.value" :label="dict.label" :value="dict.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="业务员" prop="owner">
        <el-select v-model="form.owner" placeholder="请选择业务员">
          <el-option v-for="owner in ownerList" :key="owner.userName" :label="owner.nickName" :value="owner.userName"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="customerList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" :show-overflow-tooltip="true" />
      <el-table-column label="客户名称" align="center" prop="name" :show-overflow-tooltip="true" />
      <el-table-column label="地区" align="center" prop="region" :show-overflow-tooltip="true" />
      <el-table-column label="联系人" align="center" prop="linkman" :show-overflow-tooltip="true" />
      <el-table-column label="联系电话" align="center" prop="phone" :show-overflow-tooltip="true" />
      <el-table-column label="客户级别" align="center" prop="customerRank" :show-overflow-tooltip="true" />
      <el-table-column label="客户行业" align="center" prop="customerIndustry" :show-overflow-tooltip="true" />
      <el-table-column label="最新跟进记录" align="center" prop="lastUpdateRecord" :show-overflow-tooltip="true" width="120px" />
      <el-table-column label="负责人" align="center" prop="owner" :show-overflow-tooltip="true" />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180" :show-overflow-tooltip="true">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" :page.sync="queryParams.pageNum" :limit.sync="queryParams.pageSize" @pagination="getList" />
  </div>
</template>

<script>
import {
  listDealCustomer,
} from '@/api/crm/customer'
import {
  listOwner
} from '@/api/crm/owner'

export default {
  name: 'Customer',
  dicts: [
    'clues_source',
    'customer_industry',
    'clues_status',
    'customer_rank',
    'deal_status',
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
      // 是否勾选
      selected: false,
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
        owner: null,
      },
      // 表单参数
      form: {},
      // 表单校验
      rules: {
        name: [
          { required: true, message: '客户名称不能为空', trigger: 'blur' },
        ],
        linkman: [
          { required: true, message: '联系人不能为空', trigger: 'blur' },
        ],
        phone: [
          { required: true, message: '联系电话不能为空', trigger: 'blur' },
        ],
      },
      transferCustomer: false,
      toPool: false,
    }
  },
  created () {
    this.getList();
    this.getOwnerList();
  },
  methods: {
    /** 查询成交客户列表 */
    getList () {
      this.loading = true
      listDealCustomer(this.queryParams).then((response) => {
        this.customerList = response.rows
        this.total = response.total
        this.loading = false
      })
    },
    getOwnerList () {
      this.loading = true
      listOwner(this.queryParams).then((response) => {
        this.ownerList = response.data
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
      this.selected = selection.length
    },

    /** 导出按钮操作 */
    handleExport () {
      this.download(
        'crm/customer/export',
        {
          ...this.queryParams,
        },
        `customer_${new Date().getTime()}.xlsx`
      )
    },
  },
}
</script>
