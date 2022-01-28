import request from '@/utils/request'

// 查询我的线索列表
export function listPersonClues(query) {
  return request({
    url: '/crm/clues/person-list',
    method: 'get',
    params: query
  })
}

// 查询线索列表
export function listClues(query) {
  return request({
    url: '/crm/clues/list',
    method: 'get',
    params: query
  })
}

// 查询线索详细
export function getClues(id) {
  return request({
    url: '/crm/clues/' + id,
    method: 'get'
  })
}

// 新增线索
export function addClues(data) {
  return request({
    url: '/crm/clues',
    method: 'post',
    data: data
  })
}

// 修改线索
export function updateClues(data) {
  return request({
    url: '/crm/clues',
    method: 'put',
    data: data
  })
}

// 删除线索
export function delPersonClues(id) {
  return request({
    url: '/crm/clues/person/' + id,
    method: 'delete'
  })
}

// 删除线索
export function delClues(id) {
  return request({
    url: '/crm/clues/' + id,
    method: 'delete'
  })
}

//转移线索
export function transferClues(data){
  return request({
    url: '/crm/clues/transfer',
    method: 'post',
    params: data
  })
}

//转化为客户
export function toCustomer(data){
  return request({
    url: '/crm/clues/to-customer',
    method: 'put',
    data: data
  })
}
