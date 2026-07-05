---
name: image-editor-studio
description: "Python/PySide6 기반 Windows 데스크톱 이미지 편집 프로그램(포토샵/Picsart lite)의 요구사항 분석, 설계, UI, 이미징 엔진, 테스트, 패키징을 에이전트 팀이 협업하여 개발하는 풀 개발 파이프라인. '이미지 편집 프로그램 만들어줘', '포토샵 lite 개발', 'Picsart 기능 구현', '이미지 리사이즈/보정/배경제거 앱', '데스크톱 이미지 툴' 등 이미지 편집 데스크톱 애플리케이션 개발 전반에 이 스킬을 사용한다. 기존 코드가 있는 경우에도 기능 추가나 리팩토링을 지원한다. 단, 웹 기반 이미지 편집기, 모바일 앱, 순수 이미지 생성(text-to-image) AI 모델 개발은 이 스킬의 범위가 아니다."
---

# Image Editor Studio — 이미지 편집 데스크톱 앱 개발 파이프라인

Python 데스크톱 이미지 편집 프로그램의 요구사항→설계→UI→이미징 엔진→테스트→패키징을 에이전트 팀이 협업하여 개발한다.

## 실행 모드

**에이전트 팀** — 5명이 SendMessage로 직접 통신하며 교차 검증한다.

## 에이전트 구성

| 에이전트 | 파일 | 역할 | 타입 |
|---------|------|------|------|
| architect | `.claude/agents/architect.md` | 요구사항, 기술스택, 모듈구조, 기능명세 설계 | general-purpose |
| ui-designer | `.claude/agents/ui-designer.md` | PySide6 모던 UI 구현 (캔버스, 툴패널, 테마) | general-purpose |
| imaging-engineer | `.claude/agents/imaging-engineer.md` | 이미지 처리 엔진 구현 (리사이즈/보정/배경제거 등) | general-purpose |
| qa-engineer | `.claude/agents/qa-engineer.md` | 테스트 전략, 테스트 코드, 코드 리뷰 | general-purpose |
| build-packager | `.claude/agents/build-packager.md` | PyInstaller 패키징, 배포 실행파일 생성 | general-purpose |

## 워크플로우

### Phase 1: 준비 (오케스트레이터 직접 수행)

1. 사용자 입력(또는 `req_01.md` 등 요구사항 파일)에서 추출한다:
   - **앱 설명**: 만들려는 이미지 편집 기능의 범위
   - **기술 스택** (선택): 선호 GUI 프레임워크/라이브러리
   - **기존 코드** (선택): 확장할 기존 프로젝트
   - **배포 형태** (선택): 실행파일(.exe) 단일 배포 여부
2. `_workspace/` 디렉토리를 프로젝트 루트에 생성한다
3. 입력을 정리하여 `_workspace/00_input.md`에 저장한다
4. 기존 코드가 있으면 분석하고 해당 단계를 조정한다
5. 요청 범위에 따라 **실행 모드를 결정**한다 (아래 "작업 규모별 모드" 참조)

### Phase 2: 팀 구성 및 실행

| 순서 | 작업 | 담당 | 의존 | 산출물 |
|------|------|------|------|--------|
| 1 | 아키텍처 & 기능 설계 | architect | 없음 | `01_architecture.md`, `02_feature_spec.md` |
| 2a | UI 구현 | ui-designer | 작업 1 | `src/app/` |
| 2b | 이미징 엔진 구현 | imaging-engineer | 작업 1 | `src/core/` |
| 2c | 패키징 준비 | build-packager | 작업 1 | `05_build_guide.md`, 빌드 스크립트 |
| 3 | 테스트 & 리뷰 | qa-engineer | 작업 2a, 2b | `04_test_plan.md`, `06_review_report.md`, 테스트 코드 |

작업 2a(UI), 2b(이미징 엔진), 2c(패키징)는 **병렬 실행**한다. 모두 작업 1(설계)에만 의존한다.

**팀원 간 소통 흐름:**
- architect 완료 → ui-designer에게 화면 구성·core 함수 시그니처 전달, imaging-engineer에게 기능 명세·처리 파이프라인 전달, build-packager에게 기술 스택·리소스 경로 전달, qa에게 기능 요구사항 전달
- ui-designer ↔ imaging-engineer: core 함수 입출력 타입(`PIL.Image` 통일) 실시간 조율
- build-packager 완료 → 전체에게 빌드 명령·산출물 경로 공유
- qa는 모든 코드를 리뷰하고 테스트. 🔴 필수 수정 발견 시 해당 개발자에게 수정 요청 → 재작업 → 재검증 (최대 2회)

### Phase 3: 통합 및 최종 산출물

QA의 리뷰를 기반으로 최종 산출물을 정리한다:

1. 모든 코드와 문서를 확인한다
2. 리뷰의 🔴 필수 수정이 모두 반영되었는지 확인한다
3. 최종 요약을 사용자에게 보고한다:
   - 아키텍처 설계 — `_workspace/01_architecture.md`
   - 기능 명세 — `_workspace/02_feature_spec.md`
   - UI 디자인 — `_workspace/03_ui_design.md`
   - 테스트 계획 — `_workspace/04_test_plan.md`
   - 빌드 가이드 — `_workspace/05_build_guide.md`
   - 리뷰 보고서 — `_workspace/06_review_report.md`
   - 소스 코드 — `src/` 디렉토리

## 작업 규모별 모드

사용자 요청의 범위에 따라 투입 에이전트를 조절한다:

| 사용자 요청 패턴 | 실행 모드 | 투입 에이전트 |
|----------------|----------|-------------|
| "이미지 편집 프로그램 만들어줘" | **풀 파이프라인** | 5명 전원 |
| "배경 제거 기능만 추가해줘" | **기능 추가 모드** | architect + imaging-engineer + qa |
| "UI만 새로 디자인해줘" | **UI 모드** | architect + ui-designer + qa |
| "실행파일로 패키징해줘" | **패키징 모드** | build-packager 단독 |
| "이 코드 리팩토링해줘" | **리팩토링 모드** | architect + 해당 개발자 + qa |

**기존 코드 활용**: 사용자가 기존 코드를 제공하면, 아키텍트가 코드를 분석하여 확장 지점을 파악하고 필요한 에이전트만 투입한다.

## 데이터 전달 프로토콜

| 전략 | 방식 | 용도 |
|------|------|------|
| 파일 기반 | `_workspace/` + `src/` | 설계 문서 + 소스 코드 |
| 메시지 기반 | SendMessage | 타입 불일치, 코드 리뷰, 수정 요청 |
| 태스크 기반 | TaskCreate/TaskUpdate | 진행 상황 추적, 의존 관계 관리 |

## 에러 핸들링

| 에러 유형 | 전략 |
|----------|------|
| 요구사항 모호 | 시중 이미지 편집 앱의 일반적인 패턴 적용, 가정 사항 문서화 |
| 기술 스택 미지정 | architect 기본 권장 스택 적용 (PySide6 + Pillow + OpenCV + rembg) |
| 빌드/런타임 에러 | 에러 로그 분석 → 해당 개발자가 수정 → QA 재검증 |
| 에이전트 실패 | 1회 재시도 → 실패 시 해당 산출물 없이 진행, 리뷰에 명시 |
| 리뷰에서 🔴 발견 | 해당 개발자에 수정 요청 → 재작업 → 재검증 (최대 2회) |

## 테스트 시나리오

### 정상 흐름
**프롬프트**: "req_01.md 요구사항대로 이미지 편집 프로그램을 만들어줘"
**기대 결과**:
- 아키텍처: PySide6 + Pillow + OpenCV + rembg, 모듈 구조, FR 8개 이상 명세
- UI: 좌측 툴 사이드바 + 중앙 캔버스 + 우측 속성 패널, 다크 테마 적용
- 이미징 엔진: 업로드/리사이즈/품질개선/텍스트/보정/배경제거/저장 processor 구현
- 테스트: processor별 단위 테스트, 커버리지 90% 목표
- 패키징: PyInstaller 빌드 가이드, `requirements.txt`, `build.spec`

### 기존 파일 활용 흐름
**프롬프트**: "이 프로젝트에 프린트 기능만 추가해줘" + 기존 코드
**기대 결과**:
- architect가 기존 코드 분석, 프린트 관련 모듈 설계
- imaging-engineer가 프린트용 이미지 스케일링 로직 추가, ui-designer가 프린트 다이얼로그 UI 추가
- qa가 프린트 플로우 테스트

### 에러 흐름
**프롬프트**: "이미지 앱 간단하게 만들어줘"
**기대 결과**:
- 요구사항 모호 → architect가 req_01.md 수준의 기본 기능 세트(업로드/리사이즈/보정/저장)를 MVP로 제안
- 기본 스택(PySide6 + Pillow) 적용, OpenCV/rembg는 선택적 확장으로 명시
- 리뷰 보고서에 "요구사항 가정 적용" 명시

## 에이전트별 확장 스킬

개별 에이전트의 도메인 전문성을 강화하는 확장 스킬:

| 스킬 | 대상 에이전트 | 역할 |
|------|-------------|------|
| `image-processing-recipes` | imaging-engineer | Pillow/OpenCV/rembg 구체 레시피, 파라미터 가이드 |
| `modern-desktop-ui-patterns` | ui-designer | PySide6 Fluent 테마, 레이아웃, 컴포넌트 패턴 |
