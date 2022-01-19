<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="日期查询" prop="createTime">
        <el-date-picker v-model="daterangeCreateTime" size="small" style="width: 240px" value-format="yyyy-MM-dd" type="daterange" range-separator="-" start-placeholder="开始日期" end-placeholder="结束日期"></el-date-picker>
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

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="el-icon-plus" size="mini" @click="handleAdd" v-hasPermi="['crm:customer:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="el-icon-delete" size="mini" @click="handleDelete" v-hasPermi="['crm:customer:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="info" plain icon="el-icon-download" size="mini" @click="handleExport" v-hasPermi="['crm:customer:export']">导出</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="orderList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="订单编号" align="left" prop="orderNo" />
      <el-table-column label="客户名称" align="left" prop="customerName" />
      <el-table-column label="订单金额" align="left" prop="amount" />
      <el-table-column label="负责人" align="left" prop="owner" />
      <el-table-column label="备注" align="left" prop="remark" />
      <el-table-column label="状态" align="center" prop="status">
        <template slot-scope="scope">
          <dict-tag :options="dict.type.order_review_status" :value="scope.row.status" />
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button v-if="scope.row.status==0" size="mini" type="text" icon="el-icon-edit" @click="handleApprove(scope.row)" v-hasPermi="['crm:order:approve']">审核通过</el-button>
          <el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)" v-hasPermi="['crm:order:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" :page.sync="queryParams.pageNum" :limit.sync="queryParams.pageSize" @pagination="getList" />

    <!-- 添加或修改客户对话框 -->
    <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="open" width="680px" append-to-body>
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="客户名称" prop="customerId">
          <el-select v-model="form.customerId" placeholder="请选择客户">
            <el-option v-for="customer in customerList" :key="customer.id" :label="customer.name" :value="customer.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="订单编号" prop="orderNo">
          <el-input v-model="form.orderNo" placeholder="请输入订单编号" />
        </el-form-item>
        <el-form-item label="订单金额" prop="amount">
          <el-input v-model="form.amount" placeholder="请输入订单金额" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" />
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
import { listPersonOrder, getOrder, delOrder, addOrder, updateOrder, approveOrder } from "@/api/crm/order";
import { listPersonCustomers } from "@/api/crm/customer";

export default {
  name: 'Order',
  dicts: [
    'order_review_status'
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
      // 非勾选禁用
      selected: false,
      // 显示搜索条件
      showSearch: true,
      // 总条数
      total: 0,
      // 客户表格数据
      orderList: [],
      //业务员
      ownerList: [],
      //客户列表
      customerList: [],
      //时间范围
      daterangeCreateTime: [],
      // 弹出层标题
      title: '',
      // 是否显示弹出层
      open: false,
      // 查询参数
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        orderNo: null,
        customerId: null,
        owner: null,
        status: null
      },
      // 表单参数
      form: {},
      // 表单校验
      rules: {
        orderNo: [
          { required: true, message: "订单编号不能为空", trigger: "blur" }
        ],
        customerId: [
          { required: true, message: "客户ID不能为空", trigger: "blur" }
        ],
        amount: [
          { required: true, message: "订单金额不能为空", trigger: "blur" }
        ],
      },
    }
  },
  created () {
    this.getList()
    this.getPersonCustomerList();
  },
  methods: {
    /** 查询客户列表 */
    getList () {
      this.loading = true
      this.queryParams.params = {};
      if (null != this.daterangeCreateTime && '' != this.daterangeCreateTime) {
        this.queryParams.params["beginCreateTime"] = this.daterangeCreateTime[0];
        this.queryParams.params["endCreateTime"] = this.daterangeCreateTime[1];
      }
      listPersonOrder(this.queryParams).then((response) => {
        this.orderList = response.rows
        this.total = response.total
        this.loading = false
      })
    },
    /** 查询客户列表 */
    getPersonCustomerList () {
      this.loading = true
      listPersonCustomers().then((response) => {
        this.customerList = response.data
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
        orderNo: null,
        customerId: null,
        amount: null,
        owner: null,
        createBy: null,
        createTime: null,
        updateBy: null,
        updateTime: null,
        remark: null,
        status: "0"
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
      this.reset();
      this.open = true;
      this.title = "添加我的订单";
    },
    /** 修改按钮操作 */
    handleUpdate (row) {
      this.reset();
      const id = row.id || this.ids
      getOrder(id).then(response => {
        this.form = response.data;
        this.open = true;
        this.title = "修改我的订单";
      });
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs["form"].validate(valid => {
        if (valid) {
          if (this.form.id != null) {
            updateOrder(this.form).then(response => {
              this.$modal.msgSuccess("修改成功");
              this.open = false;
              this.getList();
            });
          } else {
            addOrder(this.form).then(response => {
              this.$modal.msgSuccess("新增成功");
              this.open = false;
              this.getList();
            });
          }
        }
      });
    },
    /** 删除按钮操作 */
    handleDelete (row) {
      const ids = row.id || this.ids;
      this.$modal.confirm('是否确认删除我的订单编号为"' + ids + '"的数据项？').then(function () {
        return delOrder(ids);
      }).then(() => {
        this.getList();
        this.$modal.msgSuccess("删除成功");
      }).catch(() => { });
    },
    /** 导出按钮操作 */
    handleExport () {
      this.download('crm/order/export', {
        ...this.queryParams
      }, `我的订单_${new Date().getTime()}.xlsx`)
    },
    handleApprove (row) {
      const id = row.id
      this.$modal.confirm('确认金额和客户信息,确认审核业绩吗？').then(function () {
        return approveOrder(id);
      }).then(() => {
        this.getList();
        this.$modal.msgSuccess("审核成功");
      }).catch(() => { });
    }
  },
}
</script>
