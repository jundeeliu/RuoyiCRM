import assert from 'node:assert/strict'
import test from 'node:test'
import axios from 'axios'
import Cookies from 'js-cookie'

test('existing auth cookie helpers retain token and tenant round trips', async () => {
  const jar = new Map()
  const previousDocument = globalThis.document
  globalThis.document = {
    get cookie() {
      return Array.from(jar, ([name, value]) => `${name}=${value}`).join('; ')
    },
    set cookie(value) {
      const [entry] = value.split(';')
      const [name, ...rest] = entry.split('=')
      const expires = value.match(/(?:^|;\s*)expires=([^;]+)/i)
      if (expires && new Date(expires[1]).getTime() <= Date.now()) jar.delete(name)
      else jar.set(name, rest.join('='))
    }
  }
  try {
    const { getToken, setToken, removeToken, getTenant, setTenant } =
      await import('../src/utils/auth.js')
    setToken('token-value')
    setTenant('tenant-a')
    assert.equal(getToken(), 'token-value')
    assert.equal(getTenant(), 'tenant-a')
    removeToken()
    assert.equal(getToken(), undefined)
    Cookies.remove('Tenant-Key')
    assert.equal(getTenant(), undefined)
  } finally {
    globalThis.document = previousDocument
  }
})

test('axios keeps the Authorization and tenant headers used by the API client', async () => {
  let sent
  const client = axios.create({
    adapter: async config => {
      sent = config
      return { data: { code: 200 }, status: 200, statusText: 'OK', headers: {}, config }
    }
  })
  client.interceptors.request.use(config => {
    config.headers.Authorization = 'Bearer token-value'
    config.headers.tenant = 'tenant-a'
    return config
  })
  const response = await client.get('/system/user/list')
  assert.equal(response.data.code, 200)
  assert.equal(sent.headers.Authorization, 'Bearer token-value')
  assert.equal(sent.headers.tenant, 'tenant-a')
})
