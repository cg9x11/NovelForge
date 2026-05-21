import { i18n } from '@renderer/i18n'
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'

export const BASE_URL: string = (() => {
  const platform = import.meta.env.VITE_APP_PLATFORM

  if (platform === 'web') {
    if (import.meta.env.DEV) {
      return ''
    }
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol || 'http:'
      const hostname = window.location.hostname || '127.0.0.1'
      return `${protocol}//${hostname}:54321`
    }
    return ''
  }

  return 'http://127.0.0.1:54321'
})()

export const API_BASE_URL: string = BASE_URL
  ? `${BASE_URL.replace(/\/$/, '')}/api`
  : '/api'

interface ApiResponse<T> {
  status: 'success' | 'error'
  data: T
  message?: string
}

function translateBackendError(detail: any, fallback?: string): string {
  if (detail && typeof detail === 'object') {
    switch (detail.error_code) {
      case 'PROMPT_NOT_FOUND':
        return String(i18n.global.t('errors.promptNotFound', { name: detail.prompt_name || '' }))
      case 'PROMPT_NAME_NOT_FOUND':
        return String(i18n.global.t('errors.promptNameNotFound', { name: detail.prompt_name || '' }))
      default:
        break
    }
  }
  return fallback || String(i18n.global.t('errors.requestFailed'))
}

class HttpClient {
  private instance: AxiosInstance
  private loadingInstance: any
  private loadingCount = 0

  constructor(config: AxiosRequestConfig) {
    this.instance = axios.create(config)

    this.instance.interceptors.request.use(
      (config) => {
        const showLoading = (config as any).showLoading !== false
        if (showLoading) {
          if (this.loadingCount === 0) {
            this.loadingInstance = ElLoading.service({
              lock: true,
              text: String(i18n.global.t('common.loading')),
              background: 'rgba(0, 0, 0, 0.7)'
            })
          }
          this.loadingCount++
        }
        return config
      },
      (error) => {
        try { this.loadingCount = Math.max(0, this.loadingCount - 1); if (this.loadingCount === 0) this.loadingInstance?.close() } catch { }
        return Promise.reject(error)
      }
    )

    this.instance.interceptors.response.use(
      (response: AxiosResponse<any>) => {
        const showLoading = (response.config as any).showLoading !== false
        if (showLoading) {
          try {
            this.loadingCount = Math.max(0, this.loadingCount - 1)
            if (this.loadingCount === 0) this.loadingInstance?.close()
          } catch { }
        }
        const startedWorkflows = response.headers['x-workflows-started']
        if (startedWorkflows) {
          const runIds = startedWorkflows.split(',').map(Number)
          if (runIds.length > 0) {
            window.dispatchEvent(new CustomEvent('workflow-started', { detail: runIds }))
          }
        }

        if ((response.config as any).rawResponse === true) {
          return response as any
        }
        const res = response.data
        if (res.status === 'success' || res.status === 'error') {
          if (res.status === 'error') {
            ElMessage.error(res.message || String(i18n.global.t('common.operation_failed')))
            return Promise.reject(new Error(res.message || 'Error'))
          }
          return res.data
        }
        return res
      },
      (error) => {
        const showLoading = (error.config as any)?.showLoading !== false
        if (showLoading) {
          try {
            this.loadingCount = Math.max(0, this.loadingCount - 1)
            if (this.loadingCount === 0) this.loadingInstance?.close()
          } catch { }
        }
        if (axios.isCancel(error) || error?.code === 'ERR_CANCELED') {
          console.info('Request canceled:', error.config?.url || '')
          return Promise.reject(error)
        }
        if (error.response && error.response.status === 422) {
          const validationErrors = error.response.data.detail
          if (Array.isArray(validationErrors)) {
            const errorMessages = validationErrors.map((err: any) => {
              const fieldName = err.loc.slice(1).join(' -> ')
              return `${i18n.global.t('common.field')} '${fieldName}': ${err.msg}`
            }).join('<br/>')
            ElMessage({ type: 'error', dangerouslyUseHTMLString: true, message: `<strong>${i18n.global.t('errors.inputValidationFailed')}</strong><br/>${errorMessages}`, duration: 5000 })
          } else {
            ElMessage.error(String(i18n.global.t('errors.unknownValidationError')))
          }
        } else {
          const errorMessage = translateBackendError(error.response?.data?.detail, error.response?.data?.message || error.message || String(i18n.global.t('errors.requestFailed')))
          ElMessage.error(errorMessage)
        }
        console.error('Request error:', error.response?.data || error)
        return Promise.reject(error)
      }
    )
  }

  public request<T>(config: AxiosRequestConfig): Promise<T> {
    return this.instance.request(config)
  }

  public get<T>(url: string, params?: object, prefix: string = '/api', options?: { showLoading?: boolean, signal?: AbortSignal }): Promise<T> {
    const fullUrl = prefix ? `${prefix}${url}` : url
    return this.request<T>({ method: 'GET', url: fullUrl, params, signal: options?.signal, ...(options || {}) })
  }

  public post<T>(url: string, data?: object, prefix: string = '/api', options?: { showLoading?: boolean, signal?: AbortSignal }): Promise<T> {
    const fullUrl = prefix ? `${prefix}${url}` : url
    return this.request<T>({ method: 'POST', url: fullUrl, data, signal: options?.signal, ...(options || {}) })
  }

  public put<T>(url: string, data?: object, prefix: string = '/api', options?: { showLoading?: boolean, rawResponse?: boolean, signal?: AbortSignal }): Promise<T> {
    const fullUrl = prefix ? `${prefix}${url}` : url
    return this.request<T>({ method: 'PUT', url: fullUrl, data, signal: options?.signal, ...(options || {}) })
  }

  public delete<T>(url: string, params?: object, prefix: string = '/api', options?: { showLoading?: boolean, signal?: AbortSignal }): Promise<T> {
    const fullUrl = prefix ? `${prefix}${url}` : url
    return this.request<T>({ method: 'DELETE', url: fullUrl, params, signal: options?.signal, ...(options || {}) })
  }
}

export default new HttpClient({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

export const aiHttpClient = new HttpClient({
  baseURL: BASE_URL,
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' }
})
