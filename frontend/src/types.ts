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

export interface SrsSection {
  number: string
  title: string
  content: string
}

export interface SrsRequirement {
  req_id: string
  type: 'functional' | 'non-functional'
  title: string
  description: string
  priority: 'Must' | 'Should' | 'Could'
}

export interface SrsSummary {
  id: number
  version_no: number
  title: string
  status: 'draft' | 'approved'
  source: 'generated' | 'edited'
  note: string
  author_name: string | null
  created_at: string
  approved_by_name: string | null
  approved_at: string | null
  requirement_count: number
}

export interface SrsVersion extends SrsSummary {
  sections: SrsSection[]
  requirements: SrsRequirement[]
}

export interface SrsCompare {
  a: SrsSummary
  b: SrsSummary
  title_changed: boolean
  sections: { number: string; title: string; changed: boolean; lines: string[] }[]
  requirements: { req_id: string; before: SrsRequirement | null; after: SrsRequirement | null }[]
}
