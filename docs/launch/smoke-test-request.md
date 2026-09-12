# Second-machine smoke test request

The last red pre-launch gates: someone other than the author runs the test suite and one live
collection on their own machine. Send one of these, paste what comes back into the checklist.

What to ask for, in every case:

- the last three lines of `pytest -q`
- the printed source counts from the collect step, or the full error
- OS and chip, `python3 --version`, and whether they are on a home connection or an office/VPN
  (원티드 blocks datacenter IPs; a VPN can look like one)

---

## Korean, for a DM

안녕하세요! 구직 자동화 도구를 방금 오픈소스로 올렸는데, 제 맥북에서만 돌려봐서 남의 환경에서
깨지는지 확인이 필요합니다. 2~3분이면 됩니다. Python 3.10 이상만 있으면 됩니다.

```
git clone https://github.com/mandu5/jobradar.git && cd jobradar
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/python -m radar.collect --only saramin,jumpit
```

**부담 없는 이유:**
- 마지막 명령은 사람인·점핏 공고 목록을 한 번 읽어 로컬 JSON에 저장할 뿐입니다. 로그인·계정·API 키 없고, 아무 데도 지원하지 않고, 아무것도 보내지 않습니다.
- 개인정보를 넣을 곳이 없습니다. 프로필 파일은 없어도 돌아갑니다.

**보내주실 것:** `pytest` 마지막 3줄, collect가 출력한 소스별 건수(또는 에러 전체), OS/칩, `python3 --version`, 집 인터넷인지 회사/VPN인지. 에러가 나면 그게 제가 찾는 겁니다. 감사합니다!

---

## English, for a DM or a dev channel

Quick favour — two or three minutes, nothing to sign up for.

I just open-sourced a job-search pipeline and it has only ever run on my machine. I need one
person to confirm it installs and collects on a different setup. Python 3.10+ is the only
requirement.

```
git clone https://github.com/mandu5/jobradar.git && cd jobradar
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/python -m radar.collect --only saramin,jumpit
```

The last command reads two public Korean job boards once and writes a local JSON file. No
login, no keys, it applies to nothing and sends nothing. There is no profile to fill in for
this test.

What I need back: the last three lines of `pytest`, the per-source counts the collect step
prints (or the whole error), your OS/chip, `python3 --version`, and whether you're on a home
connection or a VPN. If it breaks, that's the bug I'm after.

---

## What a healthy run looks like

```
79 passed in 0.8s
...
[jumpit] 32
[saramin] 150
{"out": "data/candidates/2026-09-12.json", "kept": 102, "failures": {}, "stats": {"collected": 182, "kept": 102, ...}}
```

(Author's own fresh-clone run, 2026-09-12, home connection. Your numbers will differ; a
non-empty `failures` dict is what matters.)

Zero postings from *both* sources on a home connection is a finding — either a redesign broke a
parser (the fixture tests would still pass, since they're frozen) or the board is blocking. File
it as an issue the same day with the raw response saved as a fixture.
