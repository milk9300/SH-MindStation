export interface GraphNode {
  id: string
  uuid: string
  name: string
  label: string
  properties: Record<string, any>
  nodeType?: string
  style?: any
  relationships?: GraphEdge[]
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  properties: Record<string, any>
  target_name?: string
  target_uuid?: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface SchemaField {
  prop: string
  label: string
  type: 'input' | 'textarea' | 'number' | 'select' | 'rate'
  placeholder?: string
  options?: { label: string, value: any }[]
}

export interface NodeSchema {
  label: string
  fields: SchemaField[]
}
