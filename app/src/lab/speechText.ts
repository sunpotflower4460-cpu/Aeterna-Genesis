/** Keep spoken scientific qualifiers/numbers. Only presentation markup is removed.
 * Fenced code is explicitly announced as visible on screen rather than silently paraphrased. */
export function speechText(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, '\nコードや入力例は画面で確認できます。\n')
    .replace(/\[([^\]]+)\]\((?:https?:\/\/|#|\/)[^)]+\)/g, '$1')
    .replace(/(^|\n)\s*#{1,6}\s+/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/(^|\s)\*([^*\n]+)\*(?=\s|[。、！？!?.,:;]|$)/g, '$1$2')
    .replace(/(^|\n)\s*[*-]\s+/g, '$1')
    .replace(/`/g, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/** Short utterances avoid long-message stalls in some speech engines; decimals remain intact. */
export function speechChunks(text: string, max = 100): string[] {
  const normalized = speechText(text)
  if (!normalized) return []
  const sentences = normalized.match(/[^。！？!?\n]+[。！？!?]?|[。！？!?]/gu) ?? []
  const chunks: string[] = []
  let current = ''
  for (const sentence of sentences) {
    const chars = Array.from(sentence.trim())
    while (chars.length) {
      let end = Math.min(max, chars.length)
      const atom = (char: string) => /^[A-Za-z0-9_.+−-]$/.test(char)
      if (end < chars.length && atom(chars[end - 1]) && atom(chars[end])) {
        let start = end - 1
        while (start > 0 && atom(chars[start - 1])) start--
        if (start > 0) end = start
      }
      const part = chars.splice(0, end).join('')
      if (Array.from(current).length + Array.from(part).length + 1 > max && current) {
        chunks.push(current); current = ''
      }
      current += (current ? ' ' : '') + part
    }
  }
  if (current) chunks.push(current)
  return chunks
}
