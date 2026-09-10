# HTML Library

`html/` 폴더에 넣은 HTML 파일을 sidebar 목록 + iframe viewer로 보여주는 GitHub Pages 사이트입니다.
서버 코드 없이 동작하며, 파일 목록(`manifest.json`)은 push할 때마다 GitHub Actions가 생성합니다.

```
.
├── index.html                 # viewer (sidebar + iframe, hash routing)
├── html/                      # ← 여기에 HTML 파일을 넣습니다 (하위 폴더 = sidebar 그룹)
│   ├── welcome.html
│   └── examples/table-demo.html
├── scripts/build_manifest.py  # html/ 를 스캔해 manifest.json 생성 (stdlib only)
├── .github/workflows/deploy.yml
└── .nojekyll
```

## 1. 최초 설정 (한 번만)

1. 이 폴더의 내용을 `username.github.io` repo (또는 아무 repo) 에 push 합니다.
2. GitHub → repo **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 바꿉니다.
   (기본값인 "Deploy from a branch" 상태면 workflow 결과가 배포되지 않습니다.)
3. Actions 탭에서 `Deploy to GitHub Pages` 가 초록색이 되면 `https://username.github.io/` (project site면 `/repo-name/`) 에서 확인합니다.

## 2. 파일 추가

`html/` 아래에 `.html` 파일을 넣고 push 하면 끝입니다. 하위 폴더를 만들면 sidebar에서 폴더별 그룹으로 묶입니다.

- 목록에 보이는 제목: 파일의 `<title>` → 없으면 첫 `<h1>` → 없으면 파일명
- 날짜: 그 파일을 마지막으로 수정한 commit 날짜
- `.` 또는 `_` 로 시작하는 파일/폴더는 무시됩니다.
- 이미지·CSS 등을 함께 두려면 `html/` 안 어디든 두고 상대 경로로 참조하면 됩니다. (`assets/` 폴더도 있으면 함께 배포됩니다.)

특정 파일로 바로 가는 링크: `https://username.github.io/#/html/examples/table-demo.html`
viewer 상단의 **Copy link** 버튼이 이 형식의 URL을 복사합니다.

## 3. 로컬에서 확인

```bash
python scripts/build_manifest.py            # manifest.json 생성
python -m http.server 8000                  # http://localhost:8000
```

`file://` 로 직접 열면 브라우저가 `fetch('manifest.json')` 을 막으므로 반드시 로컬 서버를 띄워야 합니다.

## 4. 바꿀 수 있는 것

| 항목 | 위치 |
|---|---|
| HTML 폴더 이름 | `.github/workflows/deploy.yml` 의 `HTML_ROOT` (기본 `html`) |
| 사이트 제목 | `deploy.yml` 의 `SITE_TITLE` |
| sandbox 기본값 | `index.html` 의 `CONFIG.sandboxDefault` |
| 정렬 기본값 등 | viewer 안에서 바꾸면 브라우저 localStorage에 저장됩니다 |

## 5. Sandbox 토글에 대해

상단의 **Sandbox** 를 켜면 iframe에 `sandbox="allow-scripts allow-forms allow-popups allow-modals allow-downloads"` 가 붙습니다 (`allow-same-origin` 없음).
그 상태에서 안의 페이지는 script는 실행되지만 viewer의 DOM·cookie·localStorage에는 접근할 수 없습니다.
본인이 만든 파일만 올린다면 꺼두어도 되고, `localStorage` 를 쓰는 페이지는 sandbox 안에서 동작하지 않습니다.
sandbox는 viewer를 통해 볼 때만 적용되며, 파일 URL을 직접 열면 적용되지 않습니다.

## 6. Actions 대신 branch 배포를 쓰고 싶다면

`python scripts/build_manifest.py` 로 만든 `manifest.json` 을 repo에 함께 commit 하고, Pages Source를 "Deploy from a branch" 로 두면 workflow 없이도 동작합니다.
이 경우 파일을 추가할 때마다 manifest를 다시 생성해서 commit 해야 합니다.
