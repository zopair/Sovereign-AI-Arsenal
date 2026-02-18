'use client'

import { useQuery } from '@tanstack/react-query'
import { repositoryApi } from '@/services/api'
import { Repository } from '@/types'

interface UseRepositoriesOptions {
  filters?: {
    skip?: number
    limit?: number
    sort_by?: string
    order?: string
    category?: string
    min_score?: number
  }
}

export function useRepositories(options: UseRepositoriesOptions = {}) {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<Repository[]>({
    queryKey: ['repositories', options.filters],
    queryFn: () => repositoryApi.getRepositories(options.filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 3,
  })

  return {
    data: data || null,
    isLoading,
    error: error?.message || null,
    refetch,
  }
}