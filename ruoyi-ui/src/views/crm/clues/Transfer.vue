<template>

  <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="openTransfer" :loading="loading" @close="handleClose" @open="handleOpen" width="400px" append-to-body>
    <el-form ref="form" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="变更负责人" prop="owner">
        <el-select v-model="form.owner" placeholder="请选择员工">
          <el-option v-for="owner in ownerList" :key="owner.userName" :label="owner.nickName" :value="owner.userName"></el-option>
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
  transferClues
} from '@/api/crm/clues'
import {
  listOwner
} from '@/api/crm/owner'

export default {
  name: 'TransferCluesComponent',
  data () {
    return {
      // 遮罩层
      loading: true,
      // 弹出层标题
      title: '转移线索',
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
        owner: [
          { required: true, message: '请选择员工', trigger: 'change' },
        ],
      },
    }
  },
  created () {
    this.getOwnerList()
  },
  methods: {
    /** 查询负责人列表 */
    getOwnerList () {
      this.loading = true
      listOwner(this.queryParams).then((response) => {
        this.ownerList = response.data
        this.loading = false
      })
    },
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
        owner: undefined
      }
      this.openTransfer = false
      this.$emit("close-dialog");
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          transferClues(this.form).then((response) => {
            this.$modal.msgSuccess('转移成功')
            this.handleClose()
          })
        }
      })
    },
  },
}
</script>