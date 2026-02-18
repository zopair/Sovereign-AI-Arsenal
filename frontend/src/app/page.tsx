'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, TrendingUp, Filter, BarChart3, Code, Shield, Sparkles } from 'lucide-react'
import { SearchBar } from '@/components/search/search-bar'
import { TrendingTools } from '@/components/trending/trending-tools'
import { CategoryFilter } from '@/components/filters/category-filter'
import { StatsCards } from '@/components/stats/stats-cards'
import { SandboxResults } from '@/components/sandbox/sandbox-results'
import { useRepositories } from '@/hooks/use-repositories'
import { useSearch } from '@/hooks/use-search'
import { useCategories } from '@/hooks/use-categories'

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [showSandbox, setShowSandbox] = useState(false)

  const { 
    data: repositories, 
    isLoading: reposLoading,
    error: reposError 
  } = useRepositories()

  const {
    data: searchResults,
    isLoading: searchLoading,
    mutate: performSearch
  } = useSearch()

  const {
    data: categories,
    isLoading: categoriesLoading
  } = useCategories()

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (query.trim()) {
      performSearch({ query, searchType: 'semantic' })
    }
  }

  const filteredRepositories = repositories?.filter(repo => {
    if (selectedCategory && repo.classifications) {
      return repo.classifications.some((cat: any) => cat.category === selectedCategory)
    }
    return true
  }) || []

  const displayData = searchQuery ? searchResults : filteredRepositories

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900">
      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-50 glass-morphism border-b border-white/20"
      >
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.05 }}
            >
              <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">Sovereign AI Arsenal</h1>
                <p className="text-sm text-muted-foreground">AI Intelligence Platform</p>
              </div>
            </motion.div>

            <nav className="hidden md:flex items-center space-x-6">
              {[
                { icon: TrendingUp, label: 'Trending', active: !showSandbox },
                { icon: Shield, label: 'Sandbox', active: showSandbox },
                { icon: BarChart3, label: 'Analytics', active: false },
                { icon: Code, label: 'API', active: false },
              ].map(({ icon: Icon, label, active }) => (
                <motion.button
                  key={label}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => label === 'Sandbox' && setShowSandbox(!showSandbox)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                    active 
                      ? 'bg-primary/10 text-primary' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{label}</span>
                </motion.button>
              ))}
            </nav>
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto px-4 py-8">
        {/* Search Section */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="text-center mb-6">
            <motion.h2 
              className="text-4xl font-bold mb-4"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              Discover <span className="gradient-text">AI Innovation</span>
            </motion.h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Explore cutting-edge AI repositories with advanced semantic search, 
              trend analysis, and sandbox testing capabilities.
            </p>
          </div>

          <SearchBar 
            onSearch={handleSearch}
            isLoading={searchLoading}
            placeholder="Search repositories, technologies, or concepts..."
          />
        </motion.section>

        {/* Stats Cards */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <StatsCards />
        </motion.section>

        {/* Filters and Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Filters */}
          <motion.aside 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-1"
          >
            <CategoryFilter
              categories={categories || []}
              selectedCategory={selectedCategory}
              onCategoryChange={setSelectedCategory}
              isLoading={categoriesLoading}
            />
          </motion.aside>

          {/* Main Content */}
          <motion.div 
            className="lg:col-span-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {showSandbox ? (
              <SandboxResults />
            ) : (
              <TrendingTools 
                repositories={displayData}
                isLoading={reposLoading || searchLoading}
                searchQuery={searchQuery}
              />
            )}
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <motion.footer 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="border-t border-border/40 bg-card/50 mt-16"
      >
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold mb-3">Platform</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">API Documentation</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-3">Resources</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Tutorials</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Community</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-3">Company</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground transition-colors">About</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Privacy</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border/40 mt-8 pt-8 text-center text-sm text-muted-foreground">
            <p>&copy; 2024 Sovereign AI Arsenal. All rights reserved.</p>
          </div>
        </div>
      </motion.footer>
    </div>
  )
}