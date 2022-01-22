<template>

  <el-dialog :close-on-click-modal="false" :title="title" :visible.sync="openComment" :loading="loading" @close="handleClose" @open="handleOpen" width="680px" append-to-body>
    <el-timeline :reverse="true">
      <el-timeline-item v-for="(comment, index) in commentList" :key="index" :timestamp="comment.createTime">
        <strong>{{comment.createBy}}：</strong>{{comment.content}}
      </el-timeline-item>
    </el-timeline>
    <el-form ref="form" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="跟进内容" prop="content">
        <el-input type="textarea" v-model="form.content" :autosize="{ minRows: 2, maxRows: 4}" />
      </el-form-item>
      <el-form-item label="下次跟进时间" prop="nextFollowupTime">
        <el-date-picker clearable size="small" v-model="form.nextFollowupTime" :picker-options="nextFollowTimePicker" type="date" value-format="yyyy-MM-dd" placeholder="选择下次跟进时间">
        </el-date-picker>
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
  addComment,
  listCustomerComment
} from '@/api/crm/comment'

export default {
  name: 'CommentComponent',
  data () {
    return {
      // 遮罩层
      loading: true,
      // 弹出层标题
      title: '写跟进',
      // 是否显示弹出层
      openComment: false,
      commentList: [],
      // 查询参数
      queryParams: {

      },
      // 表单参数
      form: {
        customerId: undefined,
        content: undefined,
        nextFollowupTime: undefined
      },
      // 表单校验
      rules: {
        content: [
          { required: true, message: '请填写内容', trigger: 'blur' }
        ]
      },
      nextFollowTimePicker: {
        disabledDate: time => {
          return time.getTime() < Date.now();
        }
      }
    }
  },
  created () {

  },
  methods: {
    open (customerId) {
      this.form.customerId = customerId;
      this.openComment = true;
    },
    reset () {

    },
    handleOpen () {
      this.getList();
    },
    handleClose () {
      this.form = {
        customerId: undefined,
        content: undefined,
        nextFollowupTime: undefined
      }
      this.openComment = false
      this.$emit("close-dialog");
    },
    /** 提交按钮 */
    submitForm () {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          addComment(this.form).then((response) => {
            this.$modal.msgSuccess('保存成功')
            this.handleClose()
          })
        }
      })
    },
    getList () {
      listCustomerComment(this.form.customerId).then((response) => {
        this.commentList = response.data;
      });
    },

  },
}
</script>