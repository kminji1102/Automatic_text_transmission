# 보안 규칙

## 절대 금지

- `.env` 커밋 금지 — `.gitignore`에 반드시 포함
- `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY`를 코드에 하드코딩 금지
- `logs/*.csv` 커밋 금지 — 수신자 개인정보(이름, 전화번호) 포함

## 필수 사항

- 새 환경변수 추가 시 `.env.example`에도 반드시 추가
- `.gitignore` 필수 항목:

```
.env
logs/*.csv
logs/*.log
venv/
__pycache__/
*.py[cod]
.pytest_cache/
```
