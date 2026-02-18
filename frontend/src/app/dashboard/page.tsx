'use client'

import { motion } from 'framer-motion'
import { ArrowLeft, Download, Filter, Grid, List } from 'lucide-react'
import { useState } from 'react'
import { RepositoryCard } from '@/components/repository/repository-card'
import { RepositoryGrid } from '@/components/repository/repository-grid'
import { TrendChart } from '@/components/charts/trend-chart'
import { CategoryChart } from '@/components/charts/category-chart'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface DashboardProps {
  params: { slug: string }
}

export default function DashboardPage({ params }: DashboardProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d')

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900">
      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-50 glass-morphism border-b border-white/20"
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" asChild>
                <a href="/">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Home
                </a>
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
                <p className="text-sm text-muted-foreground">Comprehensive AI repository insights</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                <List className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto px-4 py-8">
        {/* Time Range Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between">
            <Tabs value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
              <TabsList>
                <TabsTrigger value="24h">24 Hours</TabsTrigger>
                <TabsTrigger value="7d">7 Days</TabsTrigger>
                <TabsTrigger value="30d">30 Days</TabsTrigger>
                <TabsTrigger value="90d">90 Days</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </motion.div>

        {/* Analytics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          {/* Trend Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Repository Trends
                </CardTitle>
                <CardDescription>
                  Star growth and activity over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TrendChart timeRange={selectedTimeRange} />
              </CardContent>
            </Card>
          </motion.div>

          {/* Category Distribution */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Filter className="w-5 h-5 mr-2" />
                  Categories
                </CardTitle>
                <CardDescription>
                  Distribution by AI categories
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CategoryChart />
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Top Performers */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Repositories</CardTitle>
              <CardDescription>
                Highest scoring repositories based on our comprehensive analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    name: 'tensorflow/tensorflow',
                    score: 0.95,
                    stars: 185000,
                    category: 'Deep Learning',
                    trend: '+12.5%'
                  },
                  {
                    name: 'pytorch/pytorch',
                    score: 0.93,
                    stars: 78000,
                    category: 'Deep Learning',
                    trend: '+8.3%'
                  },
                  {
                    name: 'huggingface/transformers',
                    score: 0.91,
                    stars: 125000,
                    category: 'NLP',
                    trend: '+15.7%'
                  },
                ].map((repo, index) => (
                  <motion.div
                    key={repo.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card/50 hover:bg-card transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-bold text-muted-foreground">#{index + 1}</div>
                      <div>
                        <div className="font-medium">{repo.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {repo.stars.toLocaleString()} stars • {repo.category}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-2">
                        <Badge variant="secondary" className="text-green-600">
                          {repo.trend}
                        </Badge>
                        <div className="text-sm font-medium">{repo.score}</div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.section>

        {/* Recent Sandbox Results */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-8"
        >
          <Card>
            <CardHeader>
              <CardTitle>Recent Sandbox Analysis</CardTitle>
              <CardDescription>
                Latest repository testing and setup complexity results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  {
                    repo: 'langchain-ai/langchain',
                    complexity: 'Low',
                    score: 0.3,
                    status: 'success',
                    time: '2m 15s'
                  },
                  {
                    repo: 'microsoft/semantic-kernel',
                    complexity: 'Medium',
                    score: 0.6,
                    status: 'warning',
                    time: '4m 32s'
                  },
                  {
                    repo: 'openai/whisper',
                    complexity: 'High',
                    score: 0.8,
                    status: 'error',
                    time: '6m 45s'
                  },
                ].map((result, index) => (
                  <motion.div
                    key={result.repo}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="p-4 rounded-lg border bg-card/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium text-sm truncate">{result.repo}</div>
                      <Badge 
                        variant={
                          result.status === 'success' ? 'default' : 
                          result.status === 'warning' ? 'secondary' : 'destructive'
                        }
                        className="text-xs"
                      >
                        {result.complexity}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Complexity: {result.score}</span>
                      <span>{result.time}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.section>
      </main>
    </div>
  )
}