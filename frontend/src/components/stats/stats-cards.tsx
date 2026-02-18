'use client'

import { motion } from 'framer-motion'
import { TrendingUp, Users, Code, Activity, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { statsApi } from '@/services/api'
import { formatNumber } from '@/lib/utils'

export function StatsCards() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => statsApi.getStatistics(),
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  })

  const statsData = stats || {
    total_repositories: 0,
    total_stars: 0,
    total_forks: 0,
    recent_activity: 0,
    top_languages: [],
    top_categories: []
  }

  const statCards = [
    {
      title: 'Total Repositories',
      value: formatNumber(statsData.total_repositories),
      icon: Code,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      change: '+12%',
      changeType: 'increase' as const,
    },
    {
      title: 'Total Stars',
      value: formatNumber(statsData.total_stars),
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      change: '+8%',
      changeType: 'increase' as const,
    },
    {
      title: 'Total Forks',
      value: formatNumber(statsData.total_forks),
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
      change: '+5%',
      changeType: 'increase' as const,
    },
    {
      title: 'Recent Activity',
      value: formatNumber(statsData.recent_activity),
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      change: '+15%',
      changeType: 'increase' as const,
    },
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded mb-2"></div>
                <div className="h-8 bg-muted rounded mb-2"></div>
                <div className="h-3 bg-muted rounded w-16"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat, index) => (
        <motion.div
          key={stat.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card className="card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.title}</p>
                    <p className="text-2xl font-bold">{stat.value}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`flex items-center space-x-1 text-sm ${
                    stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    <Zap className="w-3 h-3" />
                    <span>{stat.change}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">vs last period</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}