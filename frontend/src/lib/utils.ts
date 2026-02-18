import { ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function getTrendColor(trend: number): string {
  if (trend > 0.1) return 'text-green-600'
  if (trend > 0) return 'text-green-500'
  if (trend < -0.1) return 'text-red-600'
  if (trend < 0) return 'text-red-500'
  return 'text-gray-500'
}

export function getComplexityColor(score: number): string {
  if (score < 0.3) return 'text-green-600'
  if (score < 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

export function getComplexityLabel(score: number): string {
  if (score < 0.3) return 'Low'
  if (score < 0.6) return 'Medium'
  return 'High'
}