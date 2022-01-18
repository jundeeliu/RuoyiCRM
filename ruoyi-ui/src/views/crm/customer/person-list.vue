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
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="el-icon-plus" size="mini" @click="handleAdd" v-hasPermi="['crm:customer:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="warning" plain icon="el-icon-refresh-right" size="mini" :disabled="!selected" @click="handleToPool" v-hasPermi="['crm:customer:toPool']">移入公海</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="warning" plain icon="el-icon-s-promotion" size="mini" :disabled="!selected" @click="handleTransfer" v-hasPermi="['crm:customer:transfer']">转移客户</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="el-icon-delete" size="mini" @click="handleDelete" v-hasPermi="['crm:customer:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="info" plain icon="el-icon-download" size="mini" @click="handleExport" v-hasPermi="['crm:customer:export']">导出</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="customerList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" :show-overflow-tooltip="true" />
      <el-table-column label="客户名称" align="center" prop="name" :show-overflow-tooltip="true" />
      <el-table-column label="地区" align="center" prop="region" :show-overflow-tooltip="true" />
      <el-table-column label="联系人" align="center" prop="linkman" :show-overflow-tooltip="true" />
      <el-table-column label="联系电话" align="center" prop="phone" :show-overflow-tooltip="true" />
      <el-table-column label="客户级别" align="center" prop="customerRank" :show-overflow-tooltip="true" />
      <el-table-column label="客户行业" align="center" prop="customerIndustry" :show-overflow-tooltip="true" />
      <el-table-column label="成交状态" align="center" prop="dealStatus">
        <template slot-scope="scope">
          <dict-tag :options="dict.type.deal_status" :value="scope.row.dealStatus" />
        </template>
      </el-table-column>
      <el-table-column label="最新跟进记录" align="center" prop="lastUpdateRecord" :show-overflow-tooltip="true" width="120px" />
      <el-table-column label="负责人" align="center" prop="owner" :show-overflow-tooltip="true" />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180" :show-overflow-tooltip="true">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="操作" align="left" class="small-padding" width="250px">
        <template slot-scope="scope">
          <el-button size="mini" type="text" icon="el-icon-edit-outline" @click="handleComment(scope.row)" v-hasPermi="['crm:customer:comment']">写跟进</el-button>
          <el-button size="mini" type="text" icon="el-icon-s-promotion" @click="handleTransfer(scope.row)" v-hasPermi="['crm:customer:transfer']">转移</el-button>
          <el-button size="mini" type="text" icon="el-icon-edit" @click="handleUpdate(scope.row)" v-hasPermi="['crm:customer:edit']">修改</el-button>
          <el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)" v-hasPermi="['crm:customer:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" :page.sync="queryParams.pageNum" :limit.sync="queryParams.pageSize" @pagination="getList" />

    <!-- 添加或修改客户对话框 -->
    <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="open" width="680px" append-to-body>
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户编号" prop="code">
              <el-input v-model="form.code" placeholder="请输入客户编号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="联系人" prop="linkman">
              <el-input v-model="form.linkman" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="地区" prop="region">
              <el-select v-model="form.region" placeholder="请选择地区">
                <el-option v-for="dict in dict.type.region_list" :key="dict.value" :label="dict.label" :value="dict.value"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户行业" prop="customerIndustry">
              <el-select v-model="form.customerIndustry" placeholder="请选择客户行业">
                <el-option v-for="dict in dict.type.customer_industry" :key="dict.value" :label="dict.label" :value="dict.value"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="客户级别" prop="customerRank">
              <el-select v-model="form.customerRank" placeholder="请选择客户级别">
                <el-option v-for="dict in dict.type.customer_rank" :key="dict.value" :label="dict.label" :value="dict.value"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户状态" prop="customerStatus">
              <el-select v-model="form.customerStatus" placeholder="请选择客户状态">
                <el-option v-for="dict in dict.type.customer_status" :key="dict.value" :label="dict.label" :value="dict.value"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </div>
    </el-dialog>

    <TransferCustomerComponent v-if="transferCustomer" ref="transferCustomer" @close-dialog="handleTransferCustomerClose" />
    <ToPoolComponent v-if="toPool" ref="toPool" @close-dialog="handleToPoolClose" />
    <CommentComponent v-if="commentCustomer" ref="commentCustomer" @close-dialog="handleCommentClose" />
  </div>
</template>

<script>
import {
  listPersonCustomer,
  getCustomer,
  delCustomer,
  addCustomer,
  updateCustomer,
} from '@/api/crm/customer'

import TransferCustomerComponent from './Transfer'
import ToPoolComponent from './ToPool'
import CommentComponent from './Comment'

export default {
  name: 'Customer',
  components: {
    TransferCustomerComponent,
    ToPoolComponent,
    CommentComponent
  },
  dicts: [
    'clues_source',
    'customer_industry',
    'clues_status',
    'customer_rank',
    'region_list',
    'customer_status',
    'deal_status'
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
      commentCustomer: false
    }
  },
  created () {
    this.getList()
  },
  methods: {
    /** 查询客户列表 */
    getList () {
      this.loading = true
      listPersonCustomer(this.queryParams).then((response) => {
        this.customerList = response.rows
        this.total = response.total
        this.loading = false
      })
    },
    // 取消按钮
    cancel () {
      this.open = false
      this.reset()
    },
    // 表单重置
    reset () {
      this.form = {
        id: null,
        code: null,
        name: null,
        linkman: null,
        phone: null,
        region: null,
        customerIndustry: null,
        customerRank: null,
        customerStatus: null,
        status: '0',
        cluesName: null,
        cluesSource: null,
        cluesStatus: null,
        dealStatus: '0',
        owner: null,
        delFlag: null,
        version: null,
        createBy: null,
        createTime: null,
        updateBy: null,
        updateTime: null,
        remark: null,
      }
      this.resetForm('form')
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
    /** 新增按钮操作 */
    handleAdd () {
      this.reset()
      this.open = true
      this.title = '添加客户'
    },
    /** 修改按钮操作 */
    handleUpdate (row) {
      this.reset()
      const id = row.id || this.ids
      getCustomer(id).then((response) => {
        this.form = response.data
        this.open = true
        this.title = '修改客户'
      })
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          if (this.form.id != null) {
            updateCustomer(this.form).then((response) => {
              this.$modal.msgSuccess('修改成功')
              this.open = false
              this.getList()
            })
          } else {
            addCustomer(this.form).then((response) => {
              this.$modal.msgSuccess('新增成功')
              this.open = false
              this.getList()
            })
          }
        }
      })
    },
    /** 删除按钮操作 */
    handleDelete (row) {
      const ids = row.id || this.ids
      this.$modal
        .confirm('是否确认删除客户编号为"' + ids + '"的数据项？')
        .then(function () {
          return delCustomer(ids)
        })
        .then(() => {
          this.getList()
          this.$modal.msgSuccess('删除成功')
        })
        .catch(() => { })
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
    handleTransfer (row) {
      const ids = row.id || this.ids.join(",")
      this.transferCustomer = true
      this.$nextTick(() => {
        this.$refs.transferCustomer.open(ids)
      })
    },
    handleTransferCustomerClose () {
      this.transferCustomer = false;
      this.getList();
    },
    handleToPool (row) {
      const ids = row.id || this.ids.join(",")
      this.toPool = true
      this.$nextTick(() => {
        this.$refs.toPool.open(ids)
      })
    },
    handleToPoolClose () {
      this.toPool = false;
      this.getList();
    },

    handleComment (row) {
      const id = row.id
      this.commentCustomer = true
      this.$nextTick(() => {
        this.$refs.commentCustomer.open(id)
      })
    },
    handleCommentClose () {
      this.commentCustomer = false;
      this.getList();
    },
  },
}
</script>
