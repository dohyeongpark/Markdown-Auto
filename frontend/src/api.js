const BASE_URL = '/api'

// 저장소 루트는 내부적으로 "."로 표현되지만, URL 경로에 "."를 그대로 쓰면
// fetch()가 dot-segment를 정규화해 "/docs/."가 "/docs/"(목록 엔드포인트)로
// 접혀버린다. 백엔드(app/api.py)와 합의한 슬러그로 대신 보낸다.
const ROOT_DIRECTORY_SLUG = '_root'

async function request(path) {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) {
    if (response.status === 404) {
      return null
    }
    throw new Error(`API request failed: ${response.status} ${path}`)
  }
  return response.json()
}

export function listDocs(owner, repo, branch) {
  return request(`/${owner}/${repo}/${branch}/docs`)
}

export function getDoc(owner, repo, branch, directory) {
  const urlDirectory = directory === '.' ? ROOT_DIRECTORY_SLUG : directory
  // "app/clients" 처럼 슬래시를 포함할 수 있으므로 세그먼트별로 인코딩한다
  // (백엔드가 {directory:path} 컨버터로 슬래시를 그대로 기대함).
  const encodedDirectory = urlDirectory.split('/').map(encodeURIComponent).join('/')
  return request(`/${owner}/${repo}/${branch}/docs/${encodedDirectory}`)
}
