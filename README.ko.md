# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · **한국어** · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**100% AI 네이티브 스타트업을 세우세요.** 네 명의 에이전트가 당신을 위해 일하는 하나의 사무실: 그들이 제안하고, 당신이 결정합니다. 당신의 머신, 당신의 Claude 키, 당신의 데이터. 어디로도 아무것도 전송되지 않습니다.

![Zelij Core의 아쿠아리움: 창업자와 네 명의 에이전트가 대화하고, 결정을 제안하고, 승인된 것을 실행한다](docs/img/aquarium.gif)

*시뮬레이션된 하루의 아쿠아리움(여기서는 프랑스어 화면). 당신의 설치에서는 각 카드가 에이전트의 실제 행동이며, 실시간으로 표시되고 24시간 동안 다시 재생할 수 있습니다. 금색이 바로 당신입니다. 구속력 있는 일은 당신의 결정 전에는 아무것도 일어나지 않습니다. 얼굴은 모두 가상의 인물입니다.*

## 코어가 하는 일

- **사무실**: 한 페이지. 대기 중인 결정, 비서실장에게 보내는 요청, 최근 실행과 그 비용, 저널, 에이전트, 설치된 모듈.
- **결정 패킷**: 목표, 제안, 왜 지금인지, 선택지, 권고, 위험, 가역성, 계획, 롤백, 영향. 불완전한 패킷은 열리지 않습니다. 승인, 거절, 또는 에이전트에게 전달되는 필수 지시와 함께 변경 요청.
- **집안 규칙**: 구속력 있는 일(돈, 공개 노출, 삭제, 되돌릴 수 없는 일)은 결정 없이는 아무것도 일어나지 않습니다. 사실에는 날짜와 출처가 붙거나 「미검증」으로 표시됩니다. 저널은 지워지지 않습니다.
- **게이트웨이**: 창업자의 Claude 키, 사용량과 날짜가 붙은 공개 가격으로 계산되는 호출당 비용, 도달하면 차단되는 월 상한.
- **실행기**: 한정된 호출 루프(에이전트당 턴 예산), 절제된 도구, 모델의 거부는 하나의 결과로 처리.
- **모듈**: 코어를 확장하는 유일한 방법. 안정된 인터페이스, 발행자가 Ed25519로 서명한 `pack.json` 매니페스트, 모든 파일의 해시가 서명 범위에 포함, 설치 전 검증. 배포 대상과 추가 에이전트는 모두 이 길을 거칩니다.
- **재무**: 확인된 매출(읽기 전용 Stripe 가져오기 또는 증빙과 함께 직접 입력), 매달 반복되는 신고된 비용, 측정된 에이전트 비용, 월별 장부, 회계사를 위한 CSV 내보내기. 신고도 청구도 하지 않습니다.
- **연락처**: 사람당 카드 하나, 필수 법적 근거, 보존 기간, 주고받은 내용, 행사된 권리. 이의를 제기한 연락처는 더 이상 아무것도 받지 않고, 기간이 만료된 연락처는 잊히며 권리 저널만 남습니다.
- **게시**: 마케팅 에이전트가 쓴 페이지는 초안이 되고, 그다음 결정이 됩니다. 승인되면 GitHub 풀 리퀘스트 또는 WordPress 초안으로 사이트에 제안됩니다. 마지막 손길, 병합이나 게시는 당신의 몫입니다.
- **주머니 속에**: 모든 결정이 당신의 휴대폰에 도착합니다. 서명된 일회용 링크 두 개가 담긴 이메일로, 또는 버튼 세 개가 있는 Telegram으로. 지하철 줄에서 승인하면 아쿠아리움이 바로 움직입니다. 책상에서와 같은 문, 같은 저널.
- **아쿠아리움**: 에이전트가 일하는 모습을 지켜보세요. 각 거품은 최근 24시간의 실제 행동이고, 점선 고리는 빈 자리입니다. 「by zelij.ai」 배지가 붙은 공유 가능한 공개 페이지.
- **카탈로그**: 무료 에디션에 없는 것을 솔직하게 이름 붙여 나열. 발행자에게서 구매한 모듈은 여기서 서명되고 검증되어 설치됩니다. 어떤 결제도 사무실을 거치지 않습니다.
- **소프트웨어 팩토리**: 빌더는 단 하나의 저장소에서 읽고 제안하며, 보안 게이트를 통과하는 풀 리퀘스트(300줄, 텍스트만, 비밀 없음, 인프라 파일 없음, OSV로 알려진 취약점이 없는 의존성)로 제출합니다. SSH로 Linux 서버에, 또는 OVH에(API로 도메인과 DNS) 원자적 전환, 스모크 테스트, 롤백과 함께 배포. 도메인 점검, 사무실 일일 백업. 절대 병합하지 않고, 절대 결제하지 않고, 절대 사무실을 건드리지 않습니다.
- **에이전트**: 에이전트당 폴더 하나, 간단한 머리글과 프랑스어 지시가 담긴 `agent.md`. 네 명의 에이전트: Camille Aubert(비서실장), Élise Tanguy(성장, 마케팅, 제품), Nour Bellamy(재무와 고객), Sacha Ferrand(빌더, 소프트웨어 팩토리). 창업자는 사무실에서 각자에게 직접 말을 겁니다. 에이전트와 작업을 지정한 승인된 패킷은 계획의 범위 안에서 즉시 실행됩니다.

## 키 없이 1분 만에 체험

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

`http://localhost:8000`을 열고 데모에 들어가세요. 가상의 회사, 시뮬레이션된 네 명의 에이전트, 승인할 결정, 그들의 하루를 재생하는 아쿠아리움. 키도, 계정도, 비용도 없습니다. 모델에 아무것도 전송되지 않고, 중지하면 모든 것이 사라집니다. 확신이 들면 아래의 실제 설치로 넘어가세요. 사무실 자체는 프랑스어입니다.

## 시작하기

```bash
cp .env.example .env     # Claude 키, 상한, SECRET_KEY, 데이터베이스 비밀번호
docker compose up -d --build
```

사무실은 `http://localhost:8000`에서 응답합니다. SMTP가 없으면 로그인 링크가 컨테이너 로그에 기록됩니다(`docker compose logs core-app`).

전체 가이드(영어): **[설치](docs/INSTALLATION.en.md)**(빈 머신에서 https 사무실까지, SMTP, 소프트웨어 팩토리, 백업, 문제 해결), **[사용 설명서](docs/MODE-D-EMPLOI.en.md)**(각 페이지, 에이전트, 결정, 비용). 창업자와 에이전트의 사진은 [`portraits/`](portraits/README.md)에 넣습니다(설명은 프랑스어).

게시된 이미지로 로컬 빌드 없이(`.env`의 `CORE_IMAGE_TAG=v…`로 버전 고정):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Docker 없이 로컬에서:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## 발행자 공개 키

카탈로그의 모듈은 zelij.ai가 서명합니다. `ZELIJ_CLE_PUBLIQUE`에 설정할 공개 키(`.env.example`에 이미 기재됨):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## 보안

코어가 보장하고 테스트하는 것(`tests/test_securite.py`):

- **모듈**: 모듈은 발행자의 서명(Ed25519)이 있을 때만 설치되고 실행되며, 서명은 모든 코드 파일의 SHA-256 해시를 포함합니다. 서명 후 수정, 추가, 제거된 파일이 있으면 모듈은 무효가 됩니다.
- **로그인**: 20분 유효한 일회용 링크, 데이터베이스에는 해시로 저장. 링크 요청에는 주소별, IP별, 전체 제동이 있어 사무실이 이메일 중계기가 되는 일이 없습니다. 운영 환경에서 SMTP가 설정되지 않으면 링크는 생성도 기록도 되지 않습니다.
- **폼**: HMAC 세션 쿠키, `HttpOnly`, `SameSite=Strict`, 모든 POST에 출처 검사와 세션별 CSRF 방지 토큰.
- **페이지**: 엄격한 콘텐츠 보안 정책(`default-src 'self'`, 인라인 스크립트 없음, 프레임 없음), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, 출처가 https면 HSTS.
- **에이전트**: 에이전트가 읽는 것(웹 페이지, 저장소 파일)은 외부 콘텐츠로 틀에 담겨 도착하며 결코 지시가 되지 않습니다. 에이전트는 자기 카드에 있는 도구만 실행하고, 비공개 데이터를 읽은 뒤에는 회사 자체 사이트만 호출할 수 있습니다. 공개 https 주소만 읽습니다(사설, 루프백, 링크 로컬 주소와 내부 이름은 리디렉션마다 거부되고, 응답 크기에는 상한이 있습니다). 보안 게이트는 비밀, 인프라 파일, 서드파티 스크립트, 프레임, 네트워크 호출을 차단합니다.
- **컨테이너**: 비특권 사용자, 읽기 전용 파일 시스템, 케이퍼빌리티 없음, 권한 상승 없음. SSH 서버의 호스트 키를 고정할 수 있습니다(`SSH_CLE_HOTE`).
- **회계 내보내기**: 스프레드시트 수식처럼 보이는 셀은 무력화됩니다.

취약점은 `securite@zelij.ai`로 신고하고, 수정 전에는 공개하지 마세요. 모든 릴리스 전에 `pip-audit -r requirements.txt`와 `bandit -r core scripts -ll`의 결과가 비어 있어야 합니다.

## 기여와 버전

`CONTRIBUTING.md`(프랑스어)는 기여가 릴리스에 들어가는 방법을 설명합니다. 배포 대상을 기여하면 해당 팩을 평생 무료로 받는다는 규칙도 포함됩니다. `SECURITY.md`는 취약점 신고 방법을, `CHANGELOG.md`는 각 버전의 변경 사항과 창업자가 해야 할 남은 일을 설명합니다.

## 테스트와 게시 검사

```bash
python -m pytest -q
python scripts/controle_publication.py
```

게시 검사는 키, IP 주소, 내부 코드, 개인 이메일 주소, 평문 비밀번호, 그리고 저장소에 결코 포함되지 않는 비공개 목록(`ZELIJ_CORE_INTERDITS`)의 용어를 거부합니다.

## 라이선스

GNU AGPL v3. Copyright (C) 2026 zelij.ai. 같은 라이선스로 변경 사항을 공개하는 조건으로 코어를 사용, 수정, 재배포할 수 있습니다. zelij.ai를 구동하는 전체 에디션은 발행자의 것으로 남습니다.

by zelij.ai — https://zelij.ai/
