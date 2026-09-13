# jobradar

Claude Code 안에서 도는 구직 파이프라인입니다. 한국·글로벌 채용 사이트를 긁어서 **내가 쓴 채점표**대로
모든 공고를 A/B/C로 매기고, 90건 대신 읽을 만한 3건만 줍니다. **지원은 절대 대신 하지 않습니다.**

[English](README.md)

![jobradar 데모: 사람인·점핏 수집 후 채점된 RADAR.md](docs/demo.gif)

## 설치

Claude Code에서:

```
/plugin marketplace add mandu5/jobradar
/plugin install jobradar@jobradar
```

그다음 이 저장소를 받아서 (`git clone https://github.com/mandu5/jobradar && cd jobradar && pip install -e .`):

```
/jobradar setup    # 질문 5개 → profile/profile.md + profile/rubric.md
/jobradar today    # 수집 → 채점 → RADAR.md
```

Python 3.10+, 의존성은 `requests` 하나. 계정도 API 키도 가입도 없습니다. 전부 내 컴퓨터에서 돌기
때문에 데이터센터 IP를 막는 원티드도 여기서는 됩니다.

설치 전에 수집기만 먼저 돌려보려면:

```
python -m radar.collect --only saramin,jumpit
```

## 하는 일

```
/jobradar setup    질문 5개: 원하는 직무(와 아닌 직무), 경력 기준, 지역, 회사 유형 순서,
                   최우선 가치 → 프로필 + 채점표
/jobradar scan     수집기 12개 → data/candidates/<오늘>.json       (네트워크만, 모델 호출 없음)
/jobradar grade    채점표 → A / B / C, 한 줄 근거 → RADAR.md
/jobradar today    scan 후 grade
```

소스: 사람인, 원티드, 점핏, 링커리어, 네이버, 라인, 우아한형제들, LinkedIn(게스트), `radar/config.py`에
적은 Greenhouse / Ashby / Lever 보드(당근, 쿠팡, Anthropic, OpenAI, Stripe 등 22개 기본 탑재), 신입
어그리게이터, 공모전.

## 하지 않는 일

1단계 — 위의 전부 — 는 **절대 지원하지 않습니다.** 읽고, 채점하고, 보고만 합니다. 선택적인 2단계
(`prompts/apply.md`)가 지원서 패키지 초안을 쓰는데, 그것도 내가 추적판에서 직접 승인한 공고에만
돌고, 제출은 여전히 사람이 합니다. 찾는 것과 지원하는 것을 한 에이전트에 두면 언젠가 내가 안 냈을
곳에 내고, 그걸 리크루터한테서 듣게 됩니다.

## 전부를 결정하는 파일 두 개

나머지는 배관입니다. 이 둘이 제품입니다:

- **`profile/profile.md`** — 내가 누구인지, 그리고 특히 **내가 아닌 것**. 약점을 빼놓으면 채점기는
  "엔지니어"라는 단어 하나로 하드웨어 직무에 A를 줍니다.
- **`profile/rubric.md`** — 하드필터, 가중치, 등급 컷. 등급이 틀리면 코드가 아니라 이 파일을 고치면
  다음 `grade`부터 반영됩니다. 예시의 규칙 하나하나가 실제로 잘못 채점된 공고에서 나왔습니다. 가장
  센 규칙은 싱겁습니다: *모집 직무 목록에 내 직무가 없으면 회사가 아무리 좋아도 C.* 가장 쓸모 있는
  규칙: *정보가 부족하면 유리하게 추측하지 말고, 등급에 상한을 걸고 무엇이 확인되면 올라가는지
  적는다.* "해당 트랙 채용인원 확인되면 A"라고 적힌 B가 낙관적인 A보다 낫습니다.

두 파일 모두 gitignore 대상이라 공개 포크에 딸려가지 않습니다.

## 무인 모드

매일 아침 알아서 돌게 하려면 같은 엔진이 두 조각으로 돕니다:

```
04:00  GitHub Actions   수집            .github/workflows/collect.yml  (cron은 주석 처리됨)
08:30  Claude 루틴      채점+정리        prompts/daily.md
22:00  Claude 루틴      지원서 초안      prompts/apply.md   (승인한 행에만)
```

왜 쪼갰나: 스케줄 루틴의 샌드박스는 외부 채용 사이트에 접속할 수 없어 수집이 불가능하고, Actions
러너는 됩니다. 둘은 커밋된 JSON 파일에서 만납니다. 이 구조가 만든 사고 — 빈 파일이 먼저 커밋되는
바람에 수집기가 "오늘 이미 했다"고 판단해 다이제스트가 조용히 비어버린 날 — 를 `prompts/daily.md`에
주석으로 남겼습니다.

> **무인 모드로 쓰면 포크는 비공개로 두세요.** 수집 결과가 커밋되기 때문에 공개 포크는 내 구직
> 활동을 공개하는 것과 같습니다. `profile/`은 gitignore로 막혀 있고, 일일 데이터는 아닙니다.

## jobradar로 취업한 사람들

아직 없습니다 — 첫 사용자가 제작자 본인이고, 구직 중입니다. jobradar가 고른 목록이 합격으로 이어지면
[취업했어요](https://github.com/mandu5/jobradar/issues/new?template=i-got-hired.yml) 이슈를 열어 주세요.
회사명은 안 적어도 됩니다. 알고 싶은 건 어떤 rubric 규칙이 결정적이었는지, 몇 건 채점해서 몇 건
지원했는지, 그리고 괜찮으시다면 개인정보를 뺀 rubric — 두 번째 예시로 여기 링크하겠습니다.

## 소스 추가

`radar/collectors/<이름>.py`에 `fetch()`/`parse()`를 만들고 `radar/collectors/__init__.py`에 등록,
`tests/fixtures/`에 응답 샘플 하나, 테스트 하나. 파서는 저장된 fixture로 테스트해서 사이트 개편이
CI에서 소리내며 깨지지, 조용히 0건을 내진 않습니다. `pytest -q` — 80개.

## 알려진 한계

- 원티드는 GitHub Actions IP를 403으로 막습니다. 집 회선에서는 됩니다.
- 채점 품질은 정확히 채점표 품질입니다. 기본 채점표는 템플릿이지 좋은 채점표가 아닙니다.
- 채점에는 Claude Code가 필요합니다. 수집기와 정리기는 어디서든 돕니다.
- 파서는 사이트 개편에 깨집니다. fixture 테스트가 그걸 조용하지 않게 만듭니다.
- 자동 지원은 없고, 의도적입니다. 채점 관련 이슈는 환영하지만 이건 설계 결정입니다.

## 라이선스

MIT.
