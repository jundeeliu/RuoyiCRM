<template>
  <div class="app-container">
    <el-form
      :model="queryParams"
      ref="queryForm"
      :inline="true"
      v-show="showSearch"
      label-width="68px"
    >
      <el-form-item label="客户编号" prop="code">
        <el-input
          v-model="queryParams.code"
          placeholder="请输入客户编号"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="客户名称" prop="name">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入客户名称"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="联系人" prop="linkman">
        <el-input
          v-model="queryParams.linkman"
          placeholder="请输入联系人"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="联系电话" prop="phone">
        <el-input
          v-model="queryParams.phone"
          placeholder="请输入联系电话"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="地区" prop="region">
        <el-select
          v-model="queryParams.region"
          placeholder="请选择地区"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.region_list"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="客户行业" prop="customerIndustry">
        <el-select
          v-model="queryParams.customerIndustry"
          placeholder="请选择客户行业"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.customer_industry"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="客户级别" prop="customerRank">
        <el-select
          v-model="queryParams.customerRank"
          placeholder="请选择客户级别"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.customer_rank"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="客户状态" prop="customerStatus">
        <el-select
          v-model="queryParams.customerStatus"
          placeholder="请选择客户状态"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.customer_status"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="线索名称" prop="cluesName">
        <el-input
          v-model="queryParams.cluesName"
          placeholder="请输入线索名称"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="线索来源" prop="cluesSource">
        <el-select
          v-model="queryParams.cluesSource"
          placeholder="请选择线索来源"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.clues_source"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="线索状态" prop="cluesStatus">
        <el-select
          v-model="queryParams.cluesStatus"
          placeholder="请选择线索状态"
          clearable
          size="small"
        >
          <el-option
            v-for="dict in dict.type.clues_status"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="负责人" prop="manager">
        <el-input
          v-model="queryParams.manager"
          placeholder="请输入负责人"
          clearable
          size="small"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          icon="el-icon-search"
          size="mini"
          @click="handleQuery"
          >搜索</el-button
        >
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery"
          >重置</el-button
        >
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-plus"
          size="mini"
          @click="handleAdd"
          v-hasPermi="['crm:customer:add']"
          >新增</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="el-icon-edit"
          size="mini"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['crm:customer:edit']"
          >修改</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['crm:customer:remove']"
          >删除</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="el-icon-download"
          size="mini"
          @click="handleExport"
          v-hasPermi="['crm:customer:export']"
          >导出</el-button
        >
      </el-col>
      <right-toolbar
        :showSearch.sync="showSearch"
        @queryTable="getList"
      ></right-toolbar>
    </el-row>

    <el-table
      v-loading="loading"
      :data="customerList"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="客户ID" align="center" prop="id" />
      <el-table-column label="客户编号" align="center" prop="code" />
      <el-table-column label="客户名称" align="center" prop="name" />
      <el-table-column label="联系人" align="center" prop="linkman" />
      <el-table-column label="联系电话" align="center" prop="phone" />
      <el-table-column label="地区" align="center" prop="region">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.region_list"
            :value="scope.row.region"
          />
        </template>
      </el-table-column>
      <el-table-column label="客户行业" align="center" prop="customerIndustry">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.customer_industry"
            :value="scope.row.customerIndustry"
          />
        </template>
      </el-table-column>
      <el-table-column label="客户级别" align="center" prop="customerRank">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.customer_rank"
            :value="scope.row.customerRank"
          />
        </template>
      </el-table-column>
      <el-table-column label="客户状态" align="center" prop="customerStatus">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.customer_status"
            :value="scope.row.customerStatus"
          />
        </template>
      </el-table-column>
      <el-table-column label="线索名称" align="center" prop="cluesName" />
      <el-table-column label="线索来源" align="center" prop="cluesSource">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.clues_source"
            :value="scope.row.cluesSource"
          />
        </template>
      </el-table-column>
      <el-table-column label="线索状态" align="center" prop="cluesStatus">
        <template slot-scope="scope">
          <dict-tag
            :options="dict.type.clues_status"
            :value="scope.row.cluesStatus"
          />
        </template>
      </el-table-column>
      <el-table-column label="负责人" align="center" prop="manager" />
      <el-table-column
        label="操作"
        align="center"
        class-name="small-padding fixed-width"
      >
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-edit"
            @click="handleUpdate(scope.row)"
            v-hasPermi="['crm:customer:edit']"
            >修改</el-button
          >
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['crm:customer:remove']"
            >删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      :page.sync="queryParams.pageNum"
      :limit.sync="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加或修改客户对话框 -->
    <el-dialog
      :close-on-click-modal="false"
      :title="title"
      :visible.sync="open"
      width="500px"
      append-to-body
    >
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="客户编号" prop="code">
          <el-input v-model="form.code" placeholder="请输入客户编号" />
        </el-form-item>
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="联系人" prop="linkman">
          <el-input v-model="form.linkman" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="地区" prop="region">
          <el-select v-model="form.region" placeholder="请选择地区">
            <el-option
              v-for="dict in dict.type.region_list"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="客户行业" prop="customerIndustry">
          <el-select
            v-model="form.customerIndustry"
            placeholder="请选择客户行业"
          >
            <el-option
              v-for="dict in dict.type.customer_industry"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="客户级别" prop="customerRank">
          <el-select v-model="form.customerRank" placeholder="请选择客户级别">
            <el-option
              v-for="dict in dict.type.customer_rank"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="客户状态" prop="customerStatus">
          <el-select v-model="form.customerStatus" placeholder="请选择客户状态">
            <el-option
              v-for="dict in dict.type.customer_status"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="线索名称" prop="cluesName">
          <el-input v-model="form.cluesName" placeholder="请输入线索名称" />
        </el-form-item>
        <el-form-item label="线索来源" prop="cluesSource">
          <el-select v-model="form.cluesSource" placeholder="请选择线索来源">
            <el-option
              v-for="dict in dict.type.clues_source"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="线索状态" prop="cluesStatus">
          <el-select v-model="form.cluesStatus" placeholder="请选择线索状态">
            <el-option
              v-for="dict in dict.type.clues_status"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            placeholder="请输入内容"
          />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  listCustomer,
  getCustomer,
  delCustomer,
  addCustomer,
  updateCustomer,
} from '@/api/crm/customer'

export default {
  name: 'Customer',
  dicts: [
    'clues_source',
    'customer_industry',
    'clues_status',
    'customer_rank',
    'region_list',
    'customer_status',
  ],
  data() {
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
  created() {
    this.getList()
  },
  methods: {
    /** 查询客户列表 */
    getList() {
      this.loading = true
      listCustomer(this.queryParams).then((response) => {
        this.customerList = response.rows
        this.total = response.total
        this.loading = false
      })
    },
    // 取消按钮
    cancel() {
      this.open = false
      this.reset()
    },
    // 表单重置
    reset() {
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
        manager: null,
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
    handleQuery() {
      this.queryParams.pageNum = 1
      this.getList()
    },
    /** 重置按钮操作 */
    resetQuery() {
      this.resetForm('queryForm')
      this.handleQuery()
    },
    // 多选框选中数据
    handleSelectionChange(selection) {
      this.ids = selection.map((item) => item.id)
      this.single = selection.length !== 1
      this.multiple = !selection.length
    },
    /** 新增按钮操作 */
    handleAdd() {
      this.reset()
      this.open = true
      this.title = '添加客户'
    },
    /** 修改按钮操作 */
    handleUpdate(row) {
      this.reset()
      const id = row.id || this.ids
      getCustomer(id).then((response) => {
        this.form = response.data
        this.open = true
        this.title = '修改客户'
      })
    },
    /** 提交按钮 */
    submitForm() {
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
    handleDelete(row) {
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
        .catch(() => {})
    },
    /** 导出按钮操作 */
    handleExport() {
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
