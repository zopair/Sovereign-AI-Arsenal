'use client'

import { motion } from 'framer-motion'
import { Shield, Clock, AlertTriangle, CheckCircle, XCircle, Timer } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SandboxResult } from '@/types'
import { formatNumber, getComplexityColor, getComplexityLabel } from '@/lib/utils'

interface SandboxResultsProps {
  repositories?: any[]
}

export function SandboxResults({ repositories = [] }: SandboxResultsProps) {
  // Mock sandbox results for demonstration
  const mockSandboxResults: SandboxResult[] = [
    {
      repository_id: '1',
      clone_success: true,
      install_success: true,
      test_success: true,
      setup_complexity_score: 0.25,
      execution_time_seconds: 125.5,
      error_logs: [],
      test_output: 'All tests passed successfully',
      dependencies: ['fastapi', 'uvicorn', 'pydantic'],
      file_structure: {
        total_files: 45,
        total_size: 2048576,
        languages: { '.py': 35, '.md': 5, '.yml': 3, '.txt': 2 },
        config_files: ['requirements.txt', 'setup.py'],
        test_files: ['test_main.py', 'test_api.py'],
        documentation_files: ['README.md', 'docs/api.md'],
        suspicious_files: [],
        directories: ['src', 'tests', 'docs']
      },
      security_issues: [],
      performance_metrics: {
        code_lines: 2500,
        comment_lines: 500,
        blank_lines: 300,
        max_file_size: 51200,
        average_file_size: 45678,
        test_coverage: 0.85,
        cyclomatic_complexity: 12
      },
      sandbox_metadata: {
        environment: 'docker',
        docker_used: true,
        execution_time: '00:02:05'
      }
    },
    {
      repository_id: '2',
      clone_success: true,
      install_success: false,
      test_success: false,
      setup_complexity_score: 0.65,
      execution_time_seconds: 245.8,
      error_logs: ['Failed to install dependencies: numpy version conflict', 'Tests could not run due to installation failure'],
      test_output: '',
      dependencies: ['numpy', 'pandas', 'scikit-learn', 'tensorflow'],
      file_structure: {
        total_files: 120,
        total_size: 10485760,
        languages: { '.py': 80, '.ipynb': 25, '.md': 10, '.yml': 5 },
        config_files: ['requirements.txt', 'environment.yml', 'Dockerfile'],
        test_files: ['test_data.py', 'test_models.py', 'test_utils.py'],
        documentation_files: ['README.md', 'docs/guide.md', 'examples/'],
        suspicious_files: ['config.json', 'secrets.example'],
        directories: ['src', 'tests', 'docs', 'examples', 'data']
      },
      security_issues: ['Potential sensitive data in config.json', 'Missing .env.example file'],
      performance_metrics: {
        code_lines: 8500,
        comment_lines: 1200,
        blank_lines: 800,
        max_file_size: 256000,
        average_file_size: 87456,
        test_coverage: 0.65,
        cyclomatic_complexity: 28
      },
      sandbox_metadata: {
        environment: 'docker',
        docker_used: true,
        execution_time: '00:04:05'
      }
    },
    {
      repository_id: '3',
      clone_success: false,
      install_success: false,
      test_success: false,
      setup_complexity_score: 0.85,
      execution_time_seconds: 45.2,
      error_logs: ['Failed to clone repository: Repository not found or access denied'],
      test_output: '',
      dependencies: [],
      file_structure: {
        total_files: 0,
        total_size: 0,
        languages: {},
        config_files: [],
        test_files: [],
        documentation_files: [],
        suspicious_files: [],
        directories: []
      },
      security_issues: ['Repository access denied'],
      performance_metrics: {
        code_lines: 0,
        comment_lines: 0,
        blank_lines: 0,
        max_file_size: 0,
        average_file_size: 0,
        test_coverage: 0,
        cyclomatic_complexity: 0
      },
      sandbox_metadata: {
        environment: 'docker',
        docker_used: true,
        execution_time: '00:00:45'
      }
    }
  ]

  const sandboxResults = mockSandboxResults

  const getStatusIcon = (result: SandboxResult) => {
    if (!result.clone_success) {
      return XCircle
    }
    if (!result.install_success) {
      return AlertTriangle
    }
    if (!result.test_success) {
      return AlertTriangle
    }
    return CheckCircle
  }

  const getStatusColor = (result: SandboxResult) => {
    if (!result.clone_success) {
      return 'text-red-600'
    }
    if (!result.install_success) {
      return 'text-yellow-600'
    }
    if (!result.test_success) {
      return 'text-yellow-600'
    }
    return 'text-green-600'
  }

  const getStatusBadge = (result: SandboxResult) => {
    if (!result.clone_success) {
      return { label: 'Failed', variant: 'destructive' as const }
    }
    if (!result.install_success) {
      return { label: 'Partial', variant: 'secondary' as const }
    }
    if (!result.test_success) {
      return { label: 'Warning', variant: 'secondary' as const }
    }
    return { label: 'Success', variant: 'default' as const }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-primary" />
          <h2 className="text-2xl font-bold">Sandbox Analysis Results</h2>
        </div>
        <Badge variant="outline" className="text-sm">
          {sandboxResults.length} repositories analyzed
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sandboxResults.map((result, index) => {
          const StatusIcon = getStatusIcon(result)
          const statusBadge = getStatusBadge(result)
          
          return (
            <motion.div
              key={result.repository_id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="card-hover">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <StatusIcon className={`w-5 h-5 ${getStatusColor(result)}`} />
                      <span>Repository #{result.repository_id}</span>
                    </CardTitle>
                    <Badge variant={statusBadge.variant} className="text-xs">
                      {statusBadge.label}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  {/* Setup Complexity */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Setup Complexity</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-muted rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${getComplexityColor(result.setup_complexity_score)}`}
                          style={{ 
                            width: `${result.setup_complexity_score * 100}%`,
                            backgroundColor: result.setup_complexity_score < 0.3 ? '#10b981' : 
                                             result.setup_complexity_score < 0.6 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                      </div>
                      <span className={`text-sm font-medium ${getComplexityColor(result.setup_complexity_score)}`}>
                        {getComplexityLabel(result.setup_complexity_score)}
                      </span>
                    </div>
                  </div>

                  {/* Execution Time */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Execution Time</span>
                    <div className="flex items-center space-x-2">
                      <Timer className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {Math.floor(result.execution_time_seconds / 60)}m {Math.round(result.execution_time_seconds % 60)}s
                      </span>
                    </div>
                  </div>

                  {/* Dependencies */}
                  {result.dependencies.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Dependencies</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {result.dependencies.slice(0, 5).map((dep) => (
                          <Badge key={dep} variant="outline" className="text-xs">
                            {dep}
                          </Badge>
                        ))}
                        {result.dependencies.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{result.dependencies.length - 5}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {/* File Structure */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Files</span>
                      <p className="font-medium">{result.file_structure.total_files}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Size</span>
                      <p className="font-medium">{formatNumber(result.file_structure.total_size)}B</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Languages</span>
                      <p className="font-medium">{Object.keys(result.file_structure.languages).length}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Test Coverage</span>
                      <p className="font-medium">
                        {result.performance_metrics.test_coverage > 0 
                          ? `${(result.performance_metrics.test_coverage * 100).toFixed(0)}%`
                          : 'N/A'
                        }
                      </p>
                    </div>
                  </div>

                  {/* Security Issues */}
                  {result.security_issues.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Security Issues</span>
                      <div className="mt-1 space-y-1">
                        {result.security_issues.slice(0, 2).map((issue, i) => (
                          <div key={i} className="text-xs text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
                            {issue}
                          </div>
                        ))}
                        {result.security_issues.length > 2 && (
                          <p className="text-xs text-muted-foreground">
                            +{result.security_issues.length - 2} more issues
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Error Logs */}
                  {result.error_logs.length > 0 && (
                    <div>
                      <span className="text-sm text-muted-foreground">Errors</span>
                      <div className="mt-1 max-h-20 overflow-y-auto">
                        {result.error_logs.map((error, i) => (
                          <div key={i} className="text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded mb-1">
                            {error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex space-x-2 pt-4 border-t border-border/50">
                    <Button variant="outline" size="sm" className="flex-1">
                      View Details
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      Re-run Analysis
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}