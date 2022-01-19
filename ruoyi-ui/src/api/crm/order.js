import request from '@/utils/request'

// 查询订单列表
export function listOrder(query) {
  return request({
    url: '/crm/order/list',
    method: 'get',
    params: query
  })
}

// 查询我的订单列表
export function listPersonOrder(query) {
  return request({
    url: '/crm/order/person-list',
    method: 'get',
    params: query
  })
}

// 查询订单详细
export function getOrder(id) {
  return request({
    url: '/crm/order/' + id,
    method: 'get'
  })
}

// 新增订单
export function addOrder(data) {
  return request({
    url: '/crm/order',
    method: 'post',
    data: data
  })
}

// 修改订单
export function updateOrder(data) {
  return request({
    url: '/crm/order',
    method: 'put',
    data: data
  })
}

// 删除订单
export function delOrder(id) {
  return request({
    url: '/crm/order/' + id,
    method: 'delete'
  })
}

//审批订单
export function approveOrder(id){
  return request({
    url: '/crm/order/approve/'+id,
    method: 'put'
  })
}
