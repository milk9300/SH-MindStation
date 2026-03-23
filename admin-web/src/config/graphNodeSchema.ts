export interface SchemaField {
  prop: string;
  label: string;
  type: 'input' | 'textarea' | 'rate' | 'select' | 'number';
  options?: { label: string; value: any }[];
  placeholder?: string;
}

export interface NodeSchema {
  label: string;
  fields: SchemaField[];
}

export const nodeSchemaDict: Record<string, NodeSchema> = {
  '心理问题': {
    label: '心理问题',
    fields: [
      { prop: '严重程度', label: '严重程度 (1-5星)', type: 'rate' },
      { prop: '描述', label: '详细描述 / 核心定义', type: 'textarea' }
    ]
  },
  '症状': {
    label: '症状',
    fields: [
      { prop: '描述', label: '临床表现详述', type: 'textarea' }
    ]
  },
  '治疗方案': {
    label: '治疗方案',
    fields: [
      { prop: '原理', label: '核心干预原理', type: 'textarea' },
      { prop: '场景', label: '适用人群与场景', type: 'textarea' }
    ]
  },
  '应对技巧': {
    label: '应对技巧',
    fields: [
      { prop: '步骤', label: '具体执行步骤', type: 'textarea' }
    ]
  },
  '校园机构': {
    label: '校园机构',
    fields: [
      { prop: '办公地点', label: '办公地点', type: 'input' },
      { prop: '联系方式', label: '联系方式 / 办公电话', type: 'input' },
    ]
  },
  '校园政策': {
    label: '校园政策',
    fields: [
      { prop: '事项', label: '政策核心要点 / 申请流程', type: 'textarea' }
    ]
  },
  '应急预案': {
    label: '应急预案',
    fields: [
      { prop: '干预话术', label: '标准干预话术', type: 'textarea' },
      { prop: '资源', label: '外部救援资源 / 热线', type: 'input' }
    ]
  },
  '心理文章': {
    label: '心理文章',
    fields: [
      { prop: 'url', label: '文章链接', type: 'input' },
      { prop: '描述', label: '文章内容简介', type: 'textarea' }
    ]
  },
  '测评量表': {
    label: '测评量表',
    fields: [
      { prop: '题目总数', label: '题库设置的题目数量', type: 'input' },
      { prop: '描述', label: '测评量表简介', type: 'textarea' }
    ]
  }
};

export const defaultSchema: NodeSchema = {
  label: '通用节点',
  fields: [
    { prop: '描述', label: '详细描述', type: 'textarea' }
  ]
};

export const getSchemaByLabel = (label: string): NodeSchema => {
  return nodeSchemaDict[label] || defaultSchema;
};
