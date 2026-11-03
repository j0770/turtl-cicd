import { beforeEach, describe, expect, it, vi } from 'vitest'
import { makeAPIRequest } from './APIRequests'
import {
  BadRequestError,
  NotFoundError,
  PermissionDeniedError,
  ServerError,
  UnauthorizedError
} from './exceptions'

const mocks = vi.hoisted(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  return {
    client: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
    store: { userIsSignedIn: vi.fn(), refreshLogin: vi.fn(), logout: vi.fn() },
    token: { value: 'initial-token' },
    router: {}
  }
})

vi.mock('axios', () => ({ default: { create: () => mocks.client } }))
vi.mock('pinia', () => ({ storeToRefs: () => ({ accessToken: mocks.token }) }))
vi.mock('@/stores/UserStore', () => ({ useUserStore: () => mocks.store }))
vi.mock('@/router', () => ({ default: mocks.router }))

describe('makeAPIRequest', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocks.token.value = 'initial-token'
    mocks.store.userIsSignedIn.mockResolvedValue(true)
    mocks.store.logout.mockResolvedValue(undefined)
  })

  it('returns response data and adds the current authorization token', async () => {
    mocks.client.get.mockResolvedValue({ status: 200, data: { title: 'Lab' } })
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).resolves.toEqual({
      statusCode: 200,
      data: { title: 'Lab' }
    })
    expect(mocks.client.get).toHaveBeenCalledWith('/catalog', {
      headers: { Authorization: 'Bearer initial-token' }
    })
  })

  it('sends public requests without an authorization header', async () => {
    mocks.client.post.mockResolvedValue({ status: 201, data: {} })
    await makeAPIRequest('/users', 'POST', false, false, { username: 'student' })
    expect(mocks.client.post).toHaveBeenCalledWith('/users', { username: 'student' }, {})
  })

  it.each([
    [400, BadRequestError],
    [401, UnauthorizedError],
    [403, PermissionDeniedError],
    [404, NotFoundError],
    [500, ServerError]
  ])('maps HTTP %s to the corresponding application error', async (status, errorType) => {
    const data = { detail: 'Request denied' }
    mocks.client.get.mockRejectedValue({ response: { status, data } })
    const result = makeAPIRequest('/catalog', 'GET', true, false)
    await expect(result).rejects.toBeInstanceOf(errorType)
    await expect(result).rejects.toMatchObject({ message: `Error ${status}: Request denied` })
    await expect(result.catch((error) => error.getData())).resolves.toEqual(data)
  })

  it('reports an unreachable backend as a server error', async () => {
    mocks.client.get.mockRejectedValue(new Error('Network unavailable'))
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).rejects.toBeInstanceOf(ServerError)
    expect(mocks.store.refreshLogin).not.toHaveBeenCalled()
  })

  it('refreshes the token once and retries with the new token', async () => {
    mocks.client.get
      .mockRejectedValueOnce({ response: { status: 401, data: { detail: 'Expired' } } })
      .mockResolvedValueOnce({ status: 200, data: { title: 'Lab' } })
    mocks.store.refreshLogin.mockImplementation(async () => {
      mocks.token.value = 'refreshed-token'
    })
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).resolves.toMatchObject({
      statusCode: 200
    })
    expect(mocks.store.refreshLogin).toHaveBeenCalledTimes(1)
    expect(mocks.client.get).toHaveBeenLastCalledWith('/catalog', {
      headers: { Authorization: 'Bearer refreshed-token' }
    })
  })

  it('stops retrying when the refreshed token is also rejected', async () => {
    mocks.client.get.mockRejectedValue({ response: { status: 401, data: { detail: 'Expired' } } })
    mocks.store.refreshLogin.mockResolvedValue(undefined)
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).rejects.toBeInstanceOf(
      UnauthorizedError
    )
    expect(mocks.store.refreshLogin).toHaveBeenCalledTimes(1)
    expect(mocks.client.get).toHaveBeenCalledTimes(2)
    expect(mocks.store.logout).toHaveBeenCalledWith(mocks.router)
  })

  it('logs out when token refresh fails with an authorization error', async () => {
    mocks.client.get.mockRejectedValue({ response: { status: 401, data: { detail: 'Expired' } } })
    mocks.store.refreshLogin.mockRejectedValue(new UnauthorizedError('Invalid refresh', {}))
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).rejects.toMatchObject({
      message: 'Your session has expired. Please sign in again.'
    })
    expect(mocks.store.logout).toHaveBeenCalledWith(mocks.router)
    expect(mocks.client.get).toHaveBeenCalledTimes(1)
  })

  it('does not refresh a session that is no longer signed in', async () => {
    mocks.client.get.mockRejectedValue({ response: { status: 401, data: { detail: 'Expired' } } })
    mocks.store.userIsSignedIn.mockResolvedValue(false)
    await expect(makeAPIRequest('/catalog', 'GET', true, true)).rejects.toBeInstanceOf(
      UnauthorizedError
    )
    expect(mocks.store.refreshLogin).not.toHaveBeenCalled()
  })
})
