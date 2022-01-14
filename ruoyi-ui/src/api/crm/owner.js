import request from '@/utils/request'

// 查询负责人列表
export function listOwner(query) {
  return request({
    url: '/crm/owner/list',
    method: 'get',
    params: query
  })
}