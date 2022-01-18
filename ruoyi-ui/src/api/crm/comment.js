import request from '@/utils/request'

// 查询跟进记录列表
export function listComment(query) {
  return request({
    url: '/crm/comment/list',
    method: 'get',
    params: query
  })
}

// 查询跟进记录列表
export function listCustomerComment(customerId) {
  return request({
    url: '/crm/comment/customer/'+customerId,
    method: 'get'
  })
}

// 查询跟进记录详细
export function getComment(id) {
  return request({
    url: '/crm/comment/' + id,
    method: 'get'
  })
}

// 新增跟进记录
export function addComment(data) {
  return request({
    url: '/crm/comment',
    method: 'post',
    data: data
  })
}

// 修改跟进记录
export function updateComment(data) {
  return request({
    url: '/crm/comment',
    method: 'put',
    data: data
  })
}

// 删除跟进记录
export function delComment(id) {
  return request({
    url: '/crm/comment/' + id,
    method: 'delete'
  })
}
