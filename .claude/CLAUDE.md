# Image Editor Studio Harness

Python 기반 Windows 데스크톱 이미지 편집 툴(포토샵/Picsart lite)의 요구사항→설계→UI→이미징 엔진→테스트→패키징을 에이전트 팀이 협업하여 개발하는 하네스.

`harness/` 폴더의 100개 레퍼런스 하네스와 동일한 구조·품질 기준(에이전트 팀 모드, 산출물 템플릿, 의존 관계, 에러 핸들링, 테스트 시나리오, 트리거 경계)을 따르되, 이 프로젝트 전용으로 새로 구성했다.

## 구조

```
.claude/
├── agents/
│   ├── architect.md            — 요구사항 분석, 기술스택 선정, 모듈 구조, 기능 명세 설계
│   ├── ui-designer.md          — PySide6 기반 모던 UI/UX 구현 (캔버스, 툴패널, 테마)
│   ├── imaging-engineer.md     — 이미지 처리 엔진 구현 (업로드/리사이즈/보정/배경제거/텍스트/프린트/저장)
│   ├── qa-engineer.md          — 테스트 전략, 단위/통합 테스트, 코드 리뷰
│   └── build-packager.md       — PyInstaller 패키징, 배포용 실행파일 생성
├── skills/
│   ├── image-editor-studio/
│   │   └── skill.md            — 오케스트레이터 (팀 조율, 워크플로우, 에러 핸들링)
│   ├── image-processing-recipes/
│   │   └── skill.md            — imaging-engineer 확장 (Pillow/OpenCV/rembg 레시피)
│   └── modern-desktop-ui-patterns/
│       └── skill.md            — ui-designer 확장 (PySide6 모던 UI 패턴, 테마)
└── CLAUDE.md                   — 이 파일
```

## 프로젝트 개요

- **목표**: 포토샵 lite / Picsart 일부 기능을 구현한 Windows 데스크톱 이미지 편집 프로그램
- **원본 요구사항**: [`req_01.md`](../req_01.md)
- **기술 스택**: Python 3.11+, PySide6(Qt6) + PySide6-Fluent-Widgets(모던 UI), Pillow + OpenCV(이미지 처리), rembg(배경 제거), PyInstaller(패키징)
- **핵심 기능**: 이미지 업로드, 크기 조절, 품질 개선, 텍스트 추가, 보정, 배경 제거, 프린트 출력, 다운로드

## 사용법

`/image-editor-studio` 스킬을 트리거하거나, "이미지 편집 프로그램 만들어줘" 같은 자연어로 요청한다.

## 산출물

모든 설계 문서는 `_workspace/`, 소스 코드는 `src/`에 생성된다:
- `_workspace/00_input.md` — 정리된 요구사항 (req_01.md 기반)
- `_workspace/01_architecture.md` — 아키텍처 설계 문서
- `_workspace/02_feature_spec.md` — 기능별 상세 명세
- `_workspace/03_ui_design.md` — UI/UX 디자인 문서
- `_workspace/04_test_plan.md` — 테스트 계획
- `_workspace/05_build_guide.md` — 패키징/배포 가이드
- `_workspace/06_review_report.md` — 리뷰 보고서
- `src/` — 소스 코드 (UI + 이미징 엔진)
