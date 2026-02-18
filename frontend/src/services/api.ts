import axios, { AxiosInstance, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any auth tokens here if needed
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred'
        toast.error(message)
        return Promise.reject(error)
      }
    )
  }

  // Generic GET request
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params })
    return response.data
  }

  // Generic POST request
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data)
    return response.data
  }

  // Generic PUT request
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data)
    return response.data
  }

  // Generic DELETE request
  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url)
    return response.data
  }
}

// Create singleton instance
const apiClient = new ApiClient()

// Repository API
export const repositoryApi = {
  // Get repositories with optional filters
  getRepositories: async (filters?: {
    skip?: number
    limit?: number
    sort_by?: string
    order?: string
    category?: string
    min_score?: number
  }) => {
    const params = new URLSearchParams()
    if (filters?.skip) params.append('skip', filters.skip.toString())
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.sort_by) params.append('sort_by', filters.sort_by)
    if (filters?.order) params.append('order', filters.order)
    if (filters?.category) params.append('category', filters.category)
    if (filters?.min_score) params.append('min_score', filters.min_score.toString())

    return apiClient.get(`/api/v1/repositories?${params}`)
  },

  // Get single repository by ID
  getRepository: async (id: string) => {
    return apiClient.get(`/api/v1/repositories/${id}`)
  },

  // Discover new repositories
  discoverRepositories: async (options?: {
    queries?: string[]
    max_repos_per_query?: number
    auto_analyze?: boolean
  }) => {
    return apiClient.post('/api/v1/discover', options)
  },

  // Analyze repository
  analyzeRepository: async (id: string, forceReanalyze?: boolean) => {
    const params = forceReanalyze ? `?force_reanalyze=${forceReanalyze}` : ''
    return apiClient.post(`/api/v1/repositories/${id}/analyze${params}`)
  },

  // Get sandbox analysis
  getSandboxAnalysis: async (id: string) => {
    return apiClient.get(`/api/v1/repositories/${id}/sandbox`)
  },

  // Run sandbox analysis
  runSandboxAnalysis: async (id: string) => {
    return apiClient.post(`/api/v1/repositories/${id}/sandbox-analyze`)
  },
}

// Search API
export const searchApi = {
  // Search repositories
  searchRepositories: async (params: {
    q: string
    search_type?: 'semantic' | 'keyword' | 'hybrid'
    skip?: number
    limit?: number
  }) => {
    const searchParams = new URLSearchParams()
    searchParams.append('q', params.q)
    if (params.search_type) searchParams.append('search_type', params.search_type)
    if (params.skip) searchParams.append('skip', params.skip.toString())
    if (params.limit) searchParams.append('limit', params.limit.toString())

    return apiClient.get(`/api/v1/search?${searchParams}`)
  },
}

// Categories API
export const categoryApi = {
  // Get all categories
  getCategories: async () => {
    return apiClient.get('/api/v1/categories')
  },
}

// Trending API
export const trendingApi = {
  // Get trending repositories
  getTrending: async (timePeriod?: 'day' | 'week' | 'month' | 'year') => {
    const params = timePeriod ? `?time_period=${timePeriod}` : ''
    return apiClient.get(`/api/v1/trending${params}`)
  },
}

// Statistics API
export const statsApi = {
  // Get platform statistics
  getStatistics: async () => {
    return apiClient.get('/api/v1/statistics')
  },

  // Get metrics
  getMetrics: async () => {
    return apiClient.get('/metrics')
  },
}

// Health API
export const healthApi = {
  // Check health status
  checkHealth: async () => {
    return apiClient.get('/health')
  },
}

// Export the main API client for custom requests
export { apiClient }

// Utility function for handling API errors
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error.message) {
    return error.message
  }
  return 'An unexpected error occurred'
}

// Utility function for API success messages
export const showSuccessToast = (message: string) => {
  toast.success(message)
}

// Utility function for API loading states
export const createLoadingKey = (operation: string, params?: any): string => {
  return `${operation}_${JSON.stringify(params)}`
}