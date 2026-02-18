'use client'

import { useQuery } from '@tanstack/react-query'
import { categoryApi } from '@/services/api'
import { Category } from '@/types'

export function useCategories() {
  const {
    data,
    isLoading,
    error,
  } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => categoryApi.getCategories(),
    staleTime: 1000 * 60 * 10, // 10 minutes
    retry: 3,
  })

  return {
    data: data || null,
    isLoading,
    error: error?.message || null,
  }
}