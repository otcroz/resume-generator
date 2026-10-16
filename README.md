# Resume Generator | JSON 기반 이력서 PDF 생성기

기존 2페이지 A4 레이아웃을 고정한 ReportLab 기반 이력서 생성기입니다. 개발직/검증직 프로필에 따라 동일한 디자인의 PDF를 생성합니다.

> **공개 저장소 안전성:** 이 저장소는 가상 인물·회사·프로젝트 데이터와 생성된 샘플 이미지만 포함합니다. 예시의 이름, 경력, 수치, 수상은 모두 가상이며 실제 이력서가 아닙니다.

## 실행

```bash
python -m pip install -r requirements.txt
export PRETENDARD_DIR=/path/to/your/fonts
python src/generate.py --profile all
python src/validate.py output/resume_developer.pdf output/resume_validation.pdf
```

Pretendard 폰트는 별도 설치가 필요하며 저장소에 포함하지 않습니다.

## 수정 위치

- `data/developer.json`, `data/validation.json`: 직무별 독립 공개 샘플 데이터
- `profiles/developer.json`, `profiles/validation.json`: 직무별 설정
- `src/generate.py`: 고정된 레이아웃
- `src/validate.py`: PDF 검사

## 개인정보 보호

실제 이름, 연락처, 사진, 고객사 정보, 검증 내용 및 원본 PDF를 공개 저장소에 올리지 마세요. 개인 데이터는 공개 저장소 밖의 비공개 작업 복사본에 보관하세요. `.gitignore`만으로 과거 커밋에서 개인정보가 제거되지는 않습니다.


`--profile developer`는 `data/developer.json`, `--profile validation`은 `data/validation.json`을 읽습니다. `--profile all`은 두 파일을 각각 사용합니다. 실제 개인 정보는 공개 저장소에 올리지 마세요.
