'use client'

import { useQuery, useMutation } from '@tanstack/react-query'
import { searchApi } from '@/services/api'
import { SearchResult } from '@/types'
import { useState } from 'react'

interface UseSearchOptions {
  query: string
  search_type?: 'semantic' | 'keyword' | 'hybrid'
  limit?: number
  skip?: number
}

export function useSearch() {
  const [searchQuery, setSearchQuery] = useState<string>('')

  const {
    data,
    isLoading,
    error,
    mutate: search,
  } = useMutation<SearchResult[], Error, UseSearchOptions>({
    mutationFn: async (options) => {
      const result = await searchApi.searchRepositories(options)
      return Array.isArray(result) ? result : []
    },
    onSuccess: (data) => {
      // Search successful
    },
    onError: (error) => {
      // Handle search error
      console.error('Search error:', error)
    },
  })

  const clearSearch = () => {
    setSearchQuery('')
  }

  return {
    data: data || null,
    isLoading,
    error: error?.message || null,
    search,
    searchQuery,
    setSearchQuery,
    clearSearch,
  }
}