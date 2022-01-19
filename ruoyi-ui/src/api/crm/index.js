import request from '@/utils/request'


export function indexData(){
	return request({
		url:'/crm/index-data/info'
	})
}