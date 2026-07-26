// 평평한 디렉토리 목록(예: "app", "app/clients/llm")을 실제 저장소 폴더 구조와
// 같은 중첩 트리로 변환한다. 자체 문서가 없는 중간 경로(예: "app/clients")도
// 구조를 보여주기 위해 노드로 만들되, doc은 null로 둔다.
export function buildDocTree(documents) {
  const root = { name: '', path: '.', doc: null, children: [] }
  const nodeByPath = new Map([['.', root]])

  const sorted = [...documents].sort((a, b) => a.directory.localeCompare(b.directory))

  for (const doc of sorted) {
    if (doc.directory === '.') {
      root.doc = doc
      continue
    }

    const parts = doc.directory.split('/')
    let parent = root
    let currentPath = ''

    for (const part of parts) {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      let node = nodeByPath.get(currentPath)
      if (!node) {
        node = { name: part, path: currentPath, doc: null, children: [] }
        nodeByPath.set(currentPath, node)
        parent.children.push(node)
      }
      parent = node
    }

    parent.doc = doc
  }

  return root
}
