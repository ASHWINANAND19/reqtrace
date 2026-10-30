export type Role = 'Analyst' | 'QA Engineer' | 'Developer' | 'Administrator'

export interface User {
  id: number
  name: string
  email: string
  role: Role
  created_at: string
}

export interface Member {
  id: number
  name: string
  email: string
  role: Role
}

export interface Project {
  id: number
  name: string
  description: string
  archived: boolean
  owner_id: number
  owner_name: string
  member_count: number
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends Project {
  members: Member[]
}

export interface RequirementInput {
  id: number
  kind: 'text' | 'file'
  filename: string | null
  content: string
  author_name: string | null
  created_at: string
}
