// Repository types
export interface Repository {
  id: string
  github_id: number
  name: string
  full_name: string
  description: string | null
  html_url: string
  language: string | null
  stars: number
  forks: number
  open_issues: number
  created_at: string
  updated_at: string
  score: number
  trend_score: number
  ai_relevance_score: number
  topics: string[] | null
  license: string | null
  classifications?: Classification[]
  sandbox_result?: SandboxResult
}

export interface Classification {
  category: string
  confidence: number
  subcategory: string | null
  tags: string[] | null
  reasoning: string | null
}

export interface SandboxResult {
  repository_id: string
  clone_success: boolean
  install_success: boolean
  test_success: boolean
  setup_complexity_score: number
  execution_time_seconds: number
  error_logs: string[]
  test_output: string
  dependencies: string[]
  file_structure: FileStructure
  security_issues: string[]
  performance_metrics: PerformanceMetrics
  sandbox_metadata: SandboxMetadata
}

export interface FileStructure {
  total_files: number
  total_size: number
  languages: Record<string, number>
  config_files: string[]
  test_files: string[]
  documentation_files: string[]
  suspicious_files: string[]
  directories: string[]
}

export interface PerformanceMetrics {
  code_lines: number
  comment_lines: number
  blank_lines: number
  max_file_size: number
  average_file_size: number
  test_coverage: number
  cyclomatic_complexity: number
}

export interface SandboxMetadata {
  environment: string
  docker_used: boolean
  workspace_size?: number
  container_id?: string
  execution_time?: string
  docker_image?: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

// Search types
export interface SearchRequest {
  query: string
  search_type?: 'semantic' | 'keyword' | 'hybrid'
  limit?: number
  skip?: number
}

export interface SearchResult {
  id: string
  name: string
  full_name: string
  description: string | null
  language: string | null
  stars: number
  forks: number
  score: number
  relevance_score: number
  updated_at: string
}

// Category types
export interface Category {
  category: string
  repository_count: number
}

// Statistics types
export interface Statistics {
  total_repositories: number
  total_stars: number
  total_forks: number
  recent_activity: number
  top_languages: Array<{ language: string; count: number }>
  top_categories: Array<{ category: string; count: number }>
}

// Trend types
export interface TrendData {
  date: string
  stars: number
  forks: number
  contributors: number
  commits: number
  weekly_growth_rate: number
  trend_score: number
}

// Chart types
export interface ChartDataPoint {
  date: string
  value: number
  label?: string
}

export interface CategoryData {
  name: string
  value: number
  color?: string
}

// Filter types
export interface RepositoryFilters {
  category?: string
  language?: string
  minStars?: number
  maxStars?: number
  minScore?: number
  maxScore?: number
  timeRange?: '24h' | '7d' | '30d' | '90d'
  sortBy?: 'stars' | 'forks' | 'updated_at' | 'score' | 'trend_score'
  sortOrder?: 'asc' | 'desc'
}

// Error types
export interface ApiError {
  message: string
  status: number
  code?: string
  details?: any
}

// UI State types
export interface LoadingState {
  isLoading: boolean
  error: string | null
}

export interface PaginationState {
  page: number
  limit: number
  total: number
  hasMore: boolean
}

// Hook return types
export interface UseRepositoriesReturn extends LoadingState {
  data: Repository[] | null
  refetch: () => void
  loadMore: () => void
}

export interface UseSearchReturn extends LoadingState {
  data: SearchResult[] | null
  search: (query: string) => void
  clearSearch: () => void
}

export interface UseCategoriesReturn extends LoadingState {
  data: Category[] | null
}