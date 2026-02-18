'use client'

import { motion } from 'framer-motion'
import { TrendingUp, Star, GitBranch, ExternalLink } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Repository } from '@/types'
import { formatNumber, formatDate, getTrendColor } from '@/lib/utils'

interface TrendingToolsProps {
  repositories: Repository[]
  isLoading: boolean
  searchQuery?: string
}

export function TrendingTools({ repositories, isLoading, searchQuery }: TrendingToolsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="h-64">
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-muted rounded mb-2"></div>
                  <div className="h-3 bg-muted rounded mb-4 w-3/4"></div>
                  <div className="h-2 bg-muted rounded mb-2"></div>
                  <div className="h-2 bg-muted rounded mb-2 w-5/6"></div>
                  <div className="flex justify-between mt-4">
                    <div className="h-6 bg-muted rounded w-16"></div>
                    <div className="h-6 bg-muted rounded w-12"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    )
  }

  if (!repositories || repositories.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12"
      >
        <div className="text-6xl mb-4">🔍</div>
        <h3 className="text-xl font-semibold mb-2">No repositories found</h3>
        <p className="text-muted-foreground">
          {searchQuery 
            ? `No repositories found for "${searchQuery}". Try a different search term.`
            : "No repositories available. Start by discovering some repositories."
          }
        </p>
      </motion.div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {searchQuery ? `Search Results for "${searchQuery}"` : 'Trending AI Repositories'}
        </h2>
        <Badge variant="secondary" className="text-sm">
          {repositories.length} repositories
        </Badge>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {repositories.map((repo, index) => (
          <motion.div
            key={repo.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -5 }}
          >
            <Card className="card-hover group cursor-pointer">
              <CardContent className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1 group-hover:text-primary transition-colors">
                      {repo.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-2">
                      {repo.full_name}
                    </p>
                    {repo.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {repo.description}
                      </p>
                    )}
                  </div>
                  <a
                    href={repo.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {repo.language && (
                    <Badge variant="secondary" className="text-xs">
                      {repo.language}
                    </Badge>
                  )}
                  {repo.classifications?.slice(0, 2).map((classification) => (
                    <Badge key={classification.category} variant="outline" className="text-xs">
                      {classification.category}
                    </Badge>
                  ))}
                  {repo.score > 0.8 && (
                    <Badge variant="default" className="text-xs">
                      Top Rated
                    </Badge>
                  )}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center space-x-2">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium">{formatNumber(repo.stars)}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <GitBranch className="w-4 h-4 text-blue-500" />
                    <span className="text-sm font-medium">{formatNumber(repo.forks)}</span>
                  </div>
                </div>

                {/* Scores */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Overall Score</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-muted rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${repo.score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium">{(repo.score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  
                  {repo.trend_score > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Trend Score</span>
                      <div className="flex items-center space-x-2">
                        <TrendingUp className={`w-3 h-3 ${getTrendColor(repo.trend_score)}`} />
                        <span className="text-xs font-medium">{(repo.trend_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-border/50">
                  <span className="text-xs text-muted-foreground">
                    Updated {formatDate(repo.updated_at)}
                  </span>
                  {repo.sandbox_result && (
                    <Badge 
                      variant={repo.sandbox_result.clone_success ? "default" : "secondary"}
                      className="text-xs"
                    >
                      Sandbox
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  )
}