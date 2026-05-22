# GPTs English Reviews Inbox

GPTs 영어 학습 앱의 리뷰 JSON/MD 파일을 여기에 둔다.

권장 위치:

```txt
data/english/gpts-reviews/inbox/
```

Nomad English Agent는 `*.json` 파일과 Markdown 안의 `json` 코드블록을 읽어 `dashboard/english.json`과 `data/english/english-notes.json`에 반영한다. Markdown 파일은 사람이 읽는 리뷰이며, 별도 JSON 파일을 받는 것이 가장 좋지만 GPTs가 Markdown 안에 JSON을 포함해 배포한 경우도 import할 수 있다.

GPTs 출력 지침은 다음 파일을 참고한다.

```txt
docs/gpts/ENGLISH_REVIEW_GPTS_INSTRUCTIONS.md
```
