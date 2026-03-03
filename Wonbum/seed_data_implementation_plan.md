# 시드 데이터 생성 시스템 구현 계획
# Seed Data Generation System Implementation Plan

> **작성일 / Created:** 2026-02-27
> **상태 / Status:** Step 1부터 순차 진행 예정
> **참조 / References:** `시드 데이터 생성 운영 가이드.pdf`, `project_understanding.md`

## Context / 배경

Agentic TA 프로젝트의 본격적인 개발에 앞서, CS1(Intro to CS) 과목의 합성 데이터셋이 필요합니다.
100명 학생 × 5개 과제 = 총 ~500개 제출물과 관련 산출물(코드, ZIP, PDF, 채점 로그 등)을 생성합니다.
이 데이터는 시스템의 채점, 피드백, 표절 탐지, 분석 기능 개발 및 테스트에 사용됩니다.

**결정 사항:**
- 채점 결과(ExecutionResult): **시뮬레이션 방식** (확률적 생성, subprocess 미사용)
- 구현 순서: **Step 1부터 순차적으로** 진행
- 최종 목표: 전체 단계를 통합하는 `generate_data.py` CLI 스크립트 완성

### ⚠️ 단계별 진행 원칙 / Step-by-Step Execution Rule

> **IMPORTANT:** Steps 2-10을 한 번에 모두 구현하지 않습니다.
> 각 Step은 **별도의 세션에서 하나씩** 순차적으로 진행합니다.
>
> **Rules:**
> 1. 한 세션에 하나의 Step만 구현 (예: Step 2만, Step 3만)
> 2. 각 Step 완료 후 검증 (import, lint, test) 통과해야 다음 Step 진행
> 3. 새 세션 시작 시 이 문서의 "진행 상황 추적" 테이블을 확인하고, 가장 먼저 ⬜ 미착수인 Step부터 진행
> 4. 이전 Step이 ✅ 완료되지 않은 상태에서 다음 Step으로 넘어가지 않음

### ⚠️ 스텝 마무리 필수 작업 / Step Finalization Checklist

> **IMPORTANT:** 각 Step의 맨 마지막에서 반드시 아래 두 가지 작업을 수행합니다.
>
> **1. 종합 코드 리뷰 & 리팩토링 / Comprehensive Code Review & Refactoring**
> - 해당 Step에서 생성/수정한 파일뿐만 아니라, **이전 Step에서 완성된 파일도 포함**하여 전체 코드를 다시 살핍니다.
> - 코드 품질, 일관성, 중복, 네이밍 컨벤션, import 정리, 불필요한 코드 제거 등을 검토합니다.
> - 필요 시 리팩토링을 수행합니다 (함수 분리, 타입 힌트 보완, 로직 개선 등).
> - ruff check + black --check 통과를 재확인합니다.
>
> **2. 상세 영어 주석 추가 / Detailed English Comments**
> - 모든 변수, 상수, 함수, 클래스, 메서드에 대해 **아주 구체적인 영어 주석/docstring**이 있는지 확인합니다.
> - 각 항목에 대해 최소한 다음 정보를 포함해야 합니다:
>   - **What**: 해당 항목이 무엇을 하는지 (기능 설명)
>   - **Where**: 어디에서 사용되는지 (어떤 모듈/함수가 이것을 import하거나 호출하는지)
>   - **Why**: 왜 이런 설계/값을 선택했는지 (해당되는 경우)
> - 주석이 누락된 부분이 있으면 반드시 추가합니다.
> - 기존 주석이 부정확하거나 불충분하면 업데이트합니다.
> - 예시 형식:
>   ```python
>   # Maximum simulated code execution time in milliseconds for normal runs.
>   # Used by: grading.py (upper bound for successful execution runtime)
>   RUNTIME_MAX_MS: int = 2_000
>   ```

### Language Rule / 언어 규칙

> **IMPORTANT:** All code, comments, docstrings, variable names, generated data, and output
> must be written **entirely in English**. This is a US graduate-level course project at
> Georgia State University. No Korean should appear in any source code, generated files,
> or data artifacts. This plan document is bilingual for internal reference only.

---

## 진행 상황 추적 / Progress Tracking

| Step | 제목 | 상태 | 완료일 |
|------|------|------|--------|
| 1 | 환경 설정 | ✅ 완료 | 2026-02-27 |
| 2 | Config + Models | ✅ 완료 | 2026-03-01 |
| 3 | 학생 & 과제 설정 | ✅ 완료 | 2026-03-02 |
| 4 | Python 코드 파일 생성 | ✅ 완료 | 2026-03-02 |
| 5 | ZIP 번들 생성 | ✅ 완료 | 2026-03-02 |
| 6 | PDF 리포트 & OCR 이미지 | ✅ 완료 | 2026-03-02 |
| 7 | 자동채점 시뮬레이션 | ✅ 완료 | 2026-03-02 |
| 8 | 표절/유사도 시뮬레이션 | ✅ 완료 | 2026-03-02 |
| 9 | 매니페스트 & 검증 | ✅ 완료 | 2026-03-02 |
| 10 | 최종 통합 (generate_data.py) | ⬜ 미착수 | |

---

## 최종 디렉토리 구조

> 시드 데이터 생성은 프로젝트의 보조 도구이므로 `make_simul_data/` 폴더로 격리합니다.

```
agentic_ta/                        (프로젝트 루트)
  agentic_ta/
    __init__.py                    (기존, 빈 파일 - 메인 패키지)
  make_simul_data/                 (시뮬레이션 데이터 생성 전용 폴더)
    __init__.py                    (패키지 마커)
    seed_data/
      __init__.py                  (패키지 마커)
      config.py                    (상수, 분포, 과제 정의)
      models.py                    (Pydantic v2 모델 - 6개 DB 스키마 + manifest)
      students.py                  (학생 프로필 생성)
      assignments.py               (5개 CS1 과제 정의 + 테스트 케이스)
      code_generator.py            (현실적인 Python 코드 생성 + 스킬 기반 변형)
      submission_builder.py        (ZIP 번들 + 디렉토리 구조)
      report_generator.py          (PDF 리포트 + OCR 손글씨 이미지)
      grading_engine.py            (채점 결과 시뮬레이션 - 확률적 생성)
      plagiarism.py                (AST 변환 기반 표절 시뮬레이션)
      manifest.py                  (manifest.json 생성)
      validator.py                 (QA: 스키마 검증, SHA256, 분포 확인)
    generate_data.py               (CLI 진입점 - 전체 파이프라인 오케스트레이션)
    tests/
      __init__.py
      test_models.py
      test_code_generator.py
      test_validator.py
```

**import 경로 예시:** `from make_simul_data.seed_data.config import MASTER_SEED`
**실행:** `python -m make_simul_data.generate_data` 또는 `cd make_simul_data && python generate_data.py`

**출력 디렉토리** (`make_simul_data/output/seed_data/`, gitignore 대상):
```
make_simul_data/output/seed_data/
  metadata/                      (CSV 테이블)
    students.csv, submissions.csv, submission_artifacts.csv,
    execution_results.csv, test_case_results.csv,
    submission_tags.csv, similarity_scores.csv
  intro_cs/Assignments/
    HW1/S001/attempt1/
      S001_HW1_attempt1.zip
      manifest.json
      grading_log.json
    ...
```

---

## Step 1: 환경 설정

**수정 파일:**
- `pyproject.toml` — `[project.optional-dependencies]`에 `seed` 그룹 추가
- `.gitignore` — `make_simul_data/output/` 추가
- `make_simul_data/__init__.py` — 빈 패키지 마커 생성
- `make_simul_data/seed_data/__init__.py` — 빈 패키지 마커 생성

**추가 의존성 (seed 그룹):**
```toml
seed = [
    "faker>=33.0.0",
    "pandas>=2.2.0",
    "reportlab>=4.2.0",
    "Pillow>=11.0.0",
    "rapidfuzz>=3.10.0",
    "jsonschema>=4.23.0",
]
```

설치: `pip install -e ".[dev,seed]"`

---

## Step 2: Config + Models

### `config.py` — 중앙 설정
- `MASTER_SEED = 42` (재현성)
- `NUM_STUDENTS = 100`, `NUM_ASSIGNMENTS = 5`
- 제출 분포: `{1: 0.60, 2: 0.30, 3: 0.10}`
- 지각율: 20%, 통과율: 75%/20%/5%
- 점수 분포: `Beta(5, 2)`, 평균 ~80점
- 실행시간: 100~2000ms, 타임아웃 30s
- 파일 크기: Python 1-10KB, ZIP 100-300KB, PDF 50-500KB
- StrEnum: `SubmissionStatus`, `ArtifactType`, `ExecutionStatus`, `TagType`, `TagSource`, `SimilarityMethod`
- `@dataclass(frozen=True)`: `AssignmentDef`, `SeedDataConfig`

### `models.py` — Pydantic v2 모델 (7개)
1. `Submission` — submission_id(UUID), student_id, assignment_id, attempt_no, submitted_at, due_at, status
2. `SubmissionArtifact` — artifact_id, submission_id(FK), artifact_type, filename, filetype(MIME), sha256, size_bytes
3. `ExecutionResult` — exec_id, submission_id, started_at, finished_at, status, exit_code, stdout, stderr, runtime_ms
4. `TestCaseResult` — test_id, exec_id, test_case_id, passed, score_awarded, output
5. `SubmissionTag` — submission_id, tag, source, confidence
6. `SimilarityScore` — sim_id, submission_id, compared_to, method, similarity_pct, flagged
7. `Manifest` + `ManifestArtifact` — 제출별 manifest.json 스키마

---

## Step 3: 학생 & 과제 설정

### `students.py`
- `StudentProfile` dataclass: student_id, name, email, skill_level(Beta분포), attempt_counts, is_late_submitter, generates_pdf
- `generate_students(num, seed)` → `list[StudentProfile]`
- Faker로 가짜 이름/이메일 생성, Beta(5,2)로 skill_level 부여

### `assignments.py`
- 5개 과제 정의 (`ASSIGNMENTS` 리스트):
  - HW1: Variables, I/O, Arithmetic (difficulty=0.2, 5 test cases)
  - HW2: Conditionals (difficulty=0.35, 6 test cases)
  - HW3: Loops (difficulty=0.5, 7 test cases)
  - HW4: Functions (difficulty=0.65, 8 test cases)
  - HW5: Lists (difficulty=0.8, 8 test cases)
- `TestCaseDef` dataclass: test_case_id, input_data, expected_output, points
- `get_test_cases(assignment_id)` → 과제별 테스트 케이스 정의

---

## Step 4: Python 코드 파일 생성

### `code_generator.py` (가장 복잡한 모듈)

**구조: Template + Variation + Error Injection**

- `CodeTemplate` — 과제 토픽별 코드 템플릿 (과제당 4~5개 변형)
- `generate_code_files(student, assignment, attempt_no, rng)` → `list[GeneratedCodeFile]`
- 과제당 3개 파일 생성:
  - `hw{n}_solution.py` (메인 솔루션, 3-7KB)
  - `hw{n}_utils.py` (헬퍼 함수, 1-3KB)
  - `test_hw{n}.py` (테스트 러너, 0.5-2KB)

**스킬 수준별 코드 품질:**
- 높음 (>0.8): PEP8, docstring, 주석, 올바른 변수명
- 중간 (0.5~0.8): 작동하지만 스타일 불일치, 일부 주석 누락
- 낮음 (<0.5): 버그 포함 (int/float 변환 누락, off-by-one, 들여쓰기 오류 등)

**시도 횟수에 따른 개선:**
- `effective_skill = min(1.0, skill_level + 0.1 * (attempt_no - 1))`

**과제별 문제 예시:**
- HW1: 섭씨→화씨 변환, 면적 계산기, 팁 계산기, BMI, 단리 계산
- HW2: 성적 등급, 윤년 판단, 요금 계산, 세금 계산
- HW3: 구구단, 피보나치, 자릿수 합, 카운트다운
- HW4: 소수 판별, 팩토리얼, 최대값 찾기, 문자열 뒤집기
- HW5: 평균 계산, 중복 제거, 정렬 병합, 빈도수 계산

---

## Step 5: ZIP 번들 생성

### `submission_builder.py`
- `SubmissionBundle` dataclass: submission, artifacts, code_files, zip_path, submission_dir
- `build_submission(student, assignment, attempt_no, code_files, output_dir)` → `SubmissionBundle`
- ZIP 생성: `zipfile.ZipFile` + `ZIP_DEFLATED`
- 경로 규칙: `output_dir/intro_cs/Assignments/HW1/S001/attempt1/`
- 파일명 규칙: `S001_HW1_attempt1.zip`
- SHA256 해시 즉시 계산
- `SubmissionArtifact` 레코드 자동 생성

---

## Step 6: PDF 리포트 & OCR 이미지

### `report_generator.py`
- **PDF** (ReportLab): ~40% 학생이 반성문 제출
  - 내용: 학생 ID, 과제 제목, Faker 생성 반성문 (2-4 단락), "배운 점", "어려웠던 점"
  - 크기: 50-500KB (단락 수와 장식 요소로 조절)
- **OCR 이미지** (Pillow): 총 100개
  - Pillow로 손글씨 시뮬레이션 (약간의 회전, 폰트 크기 변화, 노이즈)
  - PNG 형식, 100KB-1MB

---

## Step 7: 자동채점 시뮬레이션 (시뮬레이션 방식)

### `grading_engine.py`
- `simulate_grading(student, assignment, submission_id, attempt_no, rng)` → `GradingOutcome`
- 점수 계산: `random.betavariate(5, 2)` × skill_level × (1 - difficulty × 0.3)
- 통과 카테고리: ALL_PASS(75%), PARTIAL_PASS(20%), ALL_FAIL(5%) — skill_level로 조정
- 실행시간: log-normal 분포 (100~2000ms), TIMEOUT은 ALL_FAIL의 ~2%
- stdout/stderr: 템플릿 기반 생성 (예: "Test 1: PASS", "NameError: name 'x' is not defined")
- 시도별 개선: +5~15점 (최대 100점)
- **numpy 미사용** — stdlib `random.betavariate(a, b)` 사용으로 의존성 최소화

---

## Step 8: 표절/유사도 시뮬레이션

### `plagiarism.py`
- `generate_plagiarism_pairs(submissions, rng)` → `list[PlagiarismPair]`
- ~10% 제출물에 표절 시뮬레이션 적용
- **AST 변환 방법:**
  - `VariableRenamer(ast.NodeTransformer)` — 변수명/함수명 변경
  - `DeadCodeInserter(ast.NodeTransformer)` — 불필요 코드 삽입
  - `_reformat_code()` — 포맷 변경
- 유사도 계산: AST 구조 비교 또는 `rapidfuzz.fuzz.ratio()`
- 손상 파일: ~3% 제출물 (깨진 ZIP, 인코딩 오류, 대용량 바이너리)
- 태그: `SIMULATED_PLAGIARISM`, `CORRUPTED`

---

## Step 9: 매니페스트 & 검증

### `manifest.py`
- `generate_manifest(bundle)` → `Manifest`
- `write_manifest(manifest, output_dir)` — JSON 파일로 저장

### `validator.py`
- `validate_all(output_dir)` → `list[ValidationResult]`
- 검증 항목:
  1. 스키마 검증 (jsonschema)
  2. SHA256 체크섬 일치 확인
  3. 파일 존재 여부 확인
  4. 제출 수 검증
  5. 분포 검증 (시도 횟수, 지각율, 점수)
  6. 파일 크기 범위 검증

---

## Step 10: 최종 통합 — `generate_data.py`

### CLI 인터페이스
```bash
cd make_simul_data
python generate_data.py                              # 기본 (100명, 5과제)
python generate_data.py --students 50 --assignments 3 # 축소 테스트
python generate_data.py --seed 42 --output-dir out/   # 커스텀
python generate_data.py --validate-only               # 검증만 실행
python generate_data.py -v                            # 상세 로그
```
또는 프로젝트 루트에서: `python -m make_simul_data.generate_data`

### 파이프라인 실행 순서
1. 학생 프로필 생성
2. 학생 × 과제 × 시도별 반복:
   - 코드 파일 생성 → ZIP 번들 생성 → PDF 리포트 → 채점 시뮬레이션
3. OCR 이미지 생성 (100개)
4. 표절 쌍 생성
5. 손상 파일 생성
6. 매니페스트 작성
7. CSV 메타데이터 내보내기
8. 전체 검증
9. 요약 통계 출력

---

## 검증 방법 / Verification

1. **단위 테스트**: `cd make_simul_data && pytest tests/` — 모델 유효성, 코드 생성 syntax, 검증 함수
2. **통합 테스트**: `cd make_simul_data && python generate_data.py --students 5 --assignments 2` — 소규모 실행
3. **전체 실행**: `cd make_simul_data && python generate_data.py` — 100명 × 5과제
4. **검증 실행**: `cd make_simul_data && python generate_data.py --validate-only` — 생성 데이터 무결성 확인
5. **수동 검토**: `make_simul_data/output/seed_data/` 내 .py, .zip, .pdf 파일 샘플 확인

---

## 기술 스택 요약

| 카테고리 | 도구/라이브러리 |
|---------|---------------|
| 언어 | Python 3.11+ |
| 데이터 모델 | Pydantic v2 (기존 FastAPI 의존성) |
| 가짜 데이터 | Faker |
| 테이블/CSV | pandas |
| PDF 생성 | ReportLab |
| 이미지 생성 | Pillow |
| 코드 변환 | ast (stdlib) |
| 유사도 계산 | rapidfuzz |
| 스키마 검증 | jsonschema |
| 파일 처리 | zipfile, hashlib (stdlib) |
| 점수 분포 | random.betavariate (stdlib) |
