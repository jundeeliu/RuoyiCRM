import request from '@/utils/request'

// 查询客户列表
export function listCustomer(query) {
  return request({
    url: '/crm/pool/list',
    method: 'get',
    params: query
  })
}

// 领取客户
export function receiveCustomer(id){
  return request({
    url:'/crm/pool/receive/'+id,
    method: 'get'
  })
}