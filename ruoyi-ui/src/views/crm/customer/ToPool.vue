<template>

  <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="openTransfer" :loading="loading" @close="handleClose" @open="handleOpen" width="400px" append-to-body>
    <el-form ref="form" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="公海类型" prop="poolType">
        <el-select v-model="form.poolType" placeholder="请选择公海类型">
          <el-option v-for="dict in dict.type.pool_type" :key="dict.value" :label="dict.label" :value="dict.value"></el-option>
        </el-select>
      </el-form-item>
    </el-form>
    <div slot="footer" class="dialog-footer">
      <el-button type="primary" @click="submitForm">确 定</el-button>
      <el-button @click="handleClose">取 消</el-button>
    </div>
  </el-dialog>

</template>

<script>
import {
  toPool
} from '@/api/crm/customer'

export default {
  name: 'ToPoolComponent',
  dicts: [
    'pool_type',
  ],
  data () {
    return {
      // 遮罩层
      loading: true,
      // 弹出层标题
      title: '移入公海',
      // 是否显示弹出层
      openTransfer: false,
      ownerList: undefined,
      // 查询参数
      queryParams: {

      },
      // 表单参数
      form: { ids: undefined, owner: undefined },
      // 表单校验
      rules: {
        poolType: [
          { required: true, message: '请选择公海类型', trigger: 'change' },
        ],
      },
    }
  },
  created () {

  },
  methods: {
    open (ids) {
      this.form.ids = ids;
      this.openTransfer = true;
    },
    reset () {

    },
    handleOpen () {

    },
    handleClose () {
      this.form = {
        ids: undefined,
        poolType: undefined
      }
      this.openTransfer = false
      this.$emit("close-dialog");
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          toPool(this.form).then((response) => {
            this.$modal.msgSuccess('移入成功')
            this.handleClose()
          })
        }
      })
    },
  },
}
</script>