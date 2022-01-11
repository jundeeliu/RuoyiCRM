import Cookies from 'js-cookie'

const TokenKey = 'Admin-Token'

export function getToken() {
  return Cookies.get(TokenKey)
}

export function setToken(token) {
  return Cookies.set(TokenKey, token)
}

export function removeToken() {
  return Cookies.remove(TokenKey)
}

const TenantKey="Tenant-Key"

export function getTenant(){
  return Cookies.get(TenantKey)
}
export function setTenant(tenant){
  return Cookies.set(TenantKey, tenant);
}
