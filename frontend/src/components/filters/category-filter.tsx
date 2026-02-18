'use client'

import { motion } from 'framer-motion'
import { Filter, ChevronDown, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Category } from '@/types'
import { useState } from 'react'

interface CategoryFilterProps {
  categories: Category[]
  selectedCategory: string
  onCategoryChange: (category: string) => void
  isLoading?: boolean
}

export function CategoryFilter({ 
  categories, 
  selectedCategory, 
  onCategoryChange, 
  isLoading = false 
}: CategoryFilterProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const handleCategoryClick = (category: string) => {
    if (selectedCategory === category) {
      onCategoryChange('') // Clear filter
    } else {
      onCategoryChange(category)
    }
  }

  const sortedCategories = categories.sort((a, b) => b.repository_count - a.repository_count)

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
    >
      <Card>
        <CardHeader 
          className="cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <CardTitle className="flex items-center justify-between text-lg">
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5" />
              <span>Categories</span>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </CardTitle>
        </CardHeader>
        
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ 
            height: isExpanded ? 'auto' : 0, 
            opacity: isExpanded ? 1 : 0 
          }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <CardContent className="pt-0">
            {isLoading ? (
              <div className="space-y-2">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-muted rounded mb-1"></div>
                    <div className="h-3 bg-muted rounded w-16"></div>
                  </div>
                ))}
              </div>
            ) : categories.length === 0 ? (
              <p className="text-sm text-muted-foreground">No categories available</p>
            ) : (
              <div className="space-y-1">
                {/* All Categories Option */}
                <motion.button
                  onClick={() => onCategoryChange('')}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    !selectedCategory 
                      ? 'bg-primary/10 text-primary border border-primary/20' 
                      : 'hover:bg-accent'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">All Categories</span>
                    <Badge variant="outline" className="text-xs">
                      {sortedCategories.reduce((sum, cat) => sum + cat.repository_count, 0)}
                    </Badge>
                  </div>
                </motion.button>

                {/* Individual Categories */}
                {sortedCategories.map((category, index) => (
                  <motion.button
                    key={category.category}
                    onClick={() => handleCategoryClick(category.category)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedCategory === category.category
                        ? 'bg-primary/10 text-primary border border-primary/20' 
                        : 'hover:bg-accent'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.05 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          selectedCategory === category.category
                            ? 'bg-primary'
                            : 'bg-muted'
                        }`} />
                        <span className="font-medium">{category.category}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {category.repository_count}
                      </Badge>
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </CardContent>
        </motion.div>
      </Card>
    </motion.div>
  )
}