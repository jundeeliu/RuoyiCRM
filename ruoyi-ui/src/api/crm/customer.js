import request from '@/utils/request'

// 查询客户列表
export function listPersonCustomer(query) {
  return request({
    url: '/crm/customer/person-list',
    method: 'get',
    params: query
  })
}

// 查询客户列表
export function listPersonCustomers(query) {
  return request({
    url: '/crm/customer/person-customers',
    method: 'get',
    params: query
  })
}

// 查询客户列表
export function listCustomer(query) {
  return request({
    url: '/crm/customer/list',
    method: 'get',
    params: query
  })
}

// 查询成交客户列表
export function listDealCustomer(query){
  return request({
    url: '/crm/customer/deal-list',
    method: 'get',
    params: query
  })
}

// 查询客户详细
export function getCustomer(id) {
  return request({
    url: '/crm/customer/' + id,
    method: 'get'
  })
}

// 新增客户
export function addCustomer(data) {
  return request({
    url: '/crm/customer',
    method: 'post',
    data: data
  })
}

// 修改客户
export function updateCustomer(data) {
  return request({
    url: '/crm/customer',
    method: 'put',
    data: data
  })
}

// 删除客户
export function delCustomer(id) {
  return request({
    url: '/crm/customer/' + id,
    method: 'delete'
  })
}


//转移客户
export function transferCustomer(data){
  return request({
    url: '/crm/customer/transfer',
    method: 'post',
    params: data
  })
}

//移入公海
export function toPool(data){
  return request({
    url: '/crm/customer/to-pool',
    method: 'post',
    params: data
  })
}