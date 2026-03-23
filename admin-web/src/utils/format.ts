/**
 * 格式化日期时间为本地字符串
 * @param dateStr ISO 日期字符串或 Date 对象
 * @returns 格式化后的字符串 (如: 2024/3/23 15:30:00)
 */
export function formatDateTime(dateStr: string | Date | undefined | null): string {
  if (!dateStr) return '-'
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

/**
 * 格式化时间戳为简短格式 (仅日期)
 */
export function formatDateShort(dateStr: string | Date | undefined | null): string {
  if (!dateStr) return '-'
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  return date.toLocaleDateString('zh-CN')
}
