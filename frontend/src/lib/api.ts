import { QueryClient } from '@tanstack/react-query'

// API Configuration - use environment variable or fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Endpoints
export const endpoints = {
  signals: '/v1/signals',
  signal: (id: number) => `/v1/signals/${id}`,
  options: '/v1/options',
  scanner: '/v1/scanner',
  portfolio: '/v1/portfolio',
  positions: '/v1/positions',
}

// Create query client
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
    },
  },
})

// API utility functions
export const api = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },
}
