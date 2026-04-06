export type Region = 'skin' | 'lips' | 'eyes' | 'brows'

export interface StyleInfo {
  id: string
  name: string
  description: string
}

export interface MakeupStep {
  step_num: number
  name: string
  region: Region
  image: string | null
}

export interface GenerateMakeupResponse {
  style_id: string
  style_name: string
  final_image: string | null
  steps: MakeupStep[]
}
