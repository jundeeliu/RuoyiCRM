<template>

  <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="openCustomer" :loading="loading" @close="handleClose" @open="handleOpen" width="680px" append-to-body>
    <el-form ref="form" :model="form" :rules="rules" label-width="120px">
      <el-row>
        <el-col :span="12">
          <el-form-item label="线索名称" prop="cluesName">
            <el-input :disabled="true" v-model="form.cluesName" placeholder="请输入客户名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input :disabled="true" v-model="form.phone" placeholder="请输入联系电话" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="客户名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入客户名称" />
      </el-form-item>
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
    </el-form>
    <div slot="footer" class="dialog-footer">
      <el-button type="primary" @click="submitForm">确 定</el-button>
      <el-button @click="handleClose">取 消</el-button>
    </div>
  </el-dialog>

</template>

<script>
import {
  getClues,
  toCustomer,
} from '@/api/crm/clues'

export default {
  name: 'ToCustomerComponent',
  dicts: [
    'customer_rank',
    'customer_status',
  ],
  data () {
    return {
      // 遮罩层
      loading: true,
      // 弹出层标题
      title: '转化为客户',
      // 是否显示弹出层
      openCustomer: false,
      ownerList: undefined,
      // 查询参数
      queryParams: {

      },
      // 表单参数
      form: {},
      // 表单校验
      rules: {
        name: [
          { required: true, message: '请输入客户名称', trigger: 'blur' },
        ],
      },
      cluesId: undefined
    }
  },
  created () {
    // this.getOwnerList()
  },
  methods: {
    getCluesInfo () {
      getClues(this.cluesId).then((response) => {
        this.form = response.data;
      })
    },
    open (id) {
      this.cluesId = id;
      this.openCustomer = true;
    },
    handleOpen () {
      this.getCluesInfo();
    },
    handleClose () {
      this.form = {};
      this.openCustomer = false
      this.$emit("close-dialog");
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          toCustomer(this.form).then((response) => {
            this.$modal.msgSuccess('转移成功')
            this.handleClose()
          })
        }
      })
    },
  },
}
</script>