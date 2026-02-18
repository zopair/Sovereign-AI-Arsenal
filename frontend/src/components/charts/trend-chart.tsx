'use client'

import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { format } from 'date-fns'

interface TrendChartProps {
  timeRange: string
}

interface TrendData {
  date: string
  stars: number
  forks: number
  contributors: number
  commits: number
  trend_score: number
}

export function TrendChart({ timeRange }: TrendChartProps) {
  // Mock trend data - in real app, this would come from API
  const data: TrendData[] = useMemo(() => {
    const now = new Date()
    const days = timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90
    
    return Array.from({ length: days }, (_, i) => {
      const date = new Date(now)
      date.setDate(date.getDate() - (days - i - 1))
      
      const baseStars = 1000 + Math.random() * 500
      const baseForks = 200 + Math.random() * 100
      const baseContributors = 50 + Math.random() * 25
      const baseCommits = 10 + Math.random() * 20
      
      return {
        date: format(date, 'MMM dd'),
        stars: Math.floor(baseStars + i * 15 + Math.random() * 50),
        forks: Math.floor(baseForks + i * 3 + Math.random() * 20),
        contributors: Math.floor(baseContributors + i * 0.5 + Math.random() * 5),
        commits: Math.floor(baseCommits + Math.random() * 30),
        trend_score: 0.3 + Math.random() * 0.4
      }
    })
  }, [timeRange])

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorStars" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorForks" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="date" 
            className="text-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'hsl(var(--foreground))' }}
          />
          <Area
            type="monotone"
            dataKey="stars"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#colorStars)"
            name="Stars"
          />
          <Area
            type="monotone"
            dataKey="forks"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="url(#colorForks)"
            name="Forks"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CategoryChart() {
  // Mock category data - in real app, this would come from API
  const data = [
    { name: 'Deep Learning', value: 35, color: '#3b82f6' },
    { name: 'Machine Learning', value: 28, color: '#8b5cf6' },
    { name: 'Computer Vision', value: 20, color: '#10b981' },
    { name: 'NLP', value: 18, color: '#f59e0b' },
    { name: 'Reinforcement Learning', value: 12, color: '#ef4444' },
    { name: 'MLOps', value: 8, color: '#6366f1' },
  ]

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            {data.map((entry, index) => (
              <linearGradient key={index} id={`color${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={entry.color} stopOpacity={0.8}/>
                <stop offset="95%" stopColor={entry.color} stopOpacity={0}/>
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="name" 
            className="text-muted-foreground"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            className="text-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'hsl(var(--foreground))' }}
          />
          {data.map((entry, index) => (
            <Area
              key={entry.name}
              type="monotone"
              dataKey="value"
              stroke={entry.color}
              strokeWidth={2}
              fill={`url(#color${index})`}
              stackId="1"
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}