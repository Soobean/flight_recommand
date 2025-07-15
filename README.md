# 🛫 지능형 일본 항공권 분석기

**일본 여행 항공권의 가격뿐만 아니라 가치를 분석하여 최적의 선택을 도와주는 AI 기반 서비스**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.14+-green.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [🎯 프로젝트 개요](#-프로젝트-개요)
- [✨ 주요 기능](#-주요-기능)
- [🏗️ 시스템 아키텍처](#-시스템-아키텍처)
- [🚀 빠른 시작](#-빠른-시작)
- [📖 API 문서](#-api-문서)
- [🛠️ 개발 환경](#-개발-환경)
- [📊 개발 로드맵](#-개발-로드맵)
- [🤝 기여하기](#-기여하기)

## 🎯 프로젝트 개요

### 문제 인식
일본 여행 항공권 예약 시 사용자들이 직면하는 문제들:
- 단순한 가격 비교만으로는 최적의 선택이 어려움
- 시기별/시즌별 가격 변동 패턴을 파악하기 어려움
- 환율 변동에 따른 실제 비용 계산의 복잡성
- 다양한 항공사와 경로 옵션의 복잡한 비교 과정

### 우리의 솔루션
**"가격"뿐만 아니라 "가치"를 분석하는 AI 기반 항공권 분석 서비스**

## ✨ 주요 기능

### 🎯 **Phase 1: 핵심 기능 (완료 ✅)**
- **🗾 지역별 항공편 검색**: 일본 6개 주요 지역 (홋카이도, 간토, 간사이, 중부, 규슈, 오키나와)
- **📅 기간별 스마트 검색**: 3박4일, 4박5일 등 여행 기간별 최적 항공편 검색
- **💰 최저가 날짜 검색**: 유연한 일정으로 최저가 여행 날짜 발견
- **🎌 시즌/공휴일 정보**: 일본 공휴일과 시즌별 가격 영향 분석
- **⚡ 고성능 캐싱**: Redis 기반 실시간 캐싱으로 빠른 응답 속도

### 🚀 **Phase 2: AI 분석 기능 (완료 ✅)**
- **🤖 LLM 기반 항공편 분석**:
  - 가격 트렌드 분석 및 예측
  - 경로 효율성 및 편의성 점수 계산
  - 맞춤형 항공편 추천 생성
- **🔔 실시간 가격 알림**:
  - 사용자 설정 가격 하락 알림
  - 새로운 항공편 출시 알림
- **💱 환율 변환 서비스**:
  - 한국수출입은행 API 연동
  - 80+ 통화 지원 (USD, JPY, EUR, GBP 등)
  - 실시간 환율 정보 및 과거 환율 조회
  - 통화 변환 기능 (KRW ↔ 외화)
  - 캐싱 시스템으로 빠른 응답

### 🔮 **Phase 3: 가격 예측 (개발 중)**
- **📈 ML 기반 가격 예측**: scikit-learn, XGBoost 활용한 항공료 예측
- **📊 시계열 분석**: Amadeus API 기반 가격 패턴 분석
- **🎯 최적 예약 시점 추천**: 언제 예약하면 가장 저렴한지 AI 추천
- **🗄️ 데이터 수집 시스템**: 자동화된 가격 히스토리 수집

## 🏗️ 시스템 아키텍처

### 기술 스택
- **Backend**: Python 3.12 + FastAPI + Pydantic
- **외부 API**: Amadeus for Developers API, 한국수출입은행 환율 API
- **AI/ML**: OpenAI GPT, scikit-learn, XGBoost (Phase 3)
- **캐시**: Redis 7.0+
- **작업 큐**: Celery + Redis
- **모니터링**: 구조화된 로깅 (structlog)

### 서비스 구성
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     Frontend        │    │     Backend         │    │   External APIs     │
│   (React/Next.js)   │───▶│   FastAPI Server    │───▶│   Amadeus API       │
│                     │    │                     │    │   한국수출입은행 API │
└─────────────────────┘    └─────────────────────┘    │   OpenAI API        │
                                      │                └─────────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │     Redis Cache     │
                           │   + Celery Queue    │
                           └─────────────────────┘
```

## 🚀 빠른 시작

### 1. 시스템 요구사항
- **Python**: 3.12 이상
- **Redis**: 7.0 이상
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 1GB 여유 공간

### 2. 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/WiseAirPJ/flight_recommand.git
cd flight_recommand/backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는 venv\\Scripts\\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Redis 실행 (별도 터미널)
redis-server

# 환경변수 설정
cp .env .env
# .env 파일을 편집하여 필요한 API 키들을 설정

# 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 확인
서버 실행 후 브라우저에서 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **헬스 체크**: http://localhost:8000/health

## 📖 API 문서

### 🎯 핵심 API 엔드포인트

#### 지역 관리
- `GET /api/v1/regions` - 일본 지역 목록 조회
- `GET /api/v1/regions/lowest-prices` - 지역별 최저가 조회 (메인 화면용)
- `GET /api/v1/regions/{region_id}/airports` - 지역별 공항 목록

#### 항공편 검색
- `POST /api/v1/flights/search` - 기본 항공편 검색
- `POST /api/v1/flights/search-by-duration` - 기간별 항공편 검색
- `POST /api/v1/flights/cheapest-dates` - 최저가 날짜 검색

#### AI 분석 (Phase 2)
- `POST /api/v1/llm/analyze` - 고급 항공편 분석
- `POST /api/v1/llm/price-alerts` - 가격 알림 설정
- `GET /api/v1/llm/exchange-rates` - 환율 정보 조회
- `POST /api/v1/llm/currency-conversion` - 통화 변환

#### 유틸리티
- `GET /api/v1/utils/date-info` - 날짜/공휴일/시즌 정보
- `GET /api/v1/utils/airports/search` - 공항 검색 (자동완성)
- `GET /api/v1/cache/status` - 캐시 상태 조회

### 📝 API 사용 예시

```bash
# 지역별 최저가 조회
curl -X GET \"http://localhost:8000/api/v1/regions/lowest-prices\"

# 4박5일 여행 검색
curl -X POST \"http://localhost:8000/api/v1/flights/search-by-duration\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"origin\": \"ICN\",
    \"destination_region\": \"kanto\",
    \"departure_date\": \"2025-08-15\",
    \"trip_duration\": 5,
    \"adults\": 2
  }'

# 환율 변환
curl -X POST \"http://localhost:8000/api/v1/llm/currency-conversion\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"amount\": 500000,
    \"from_currency\": \"KRW\",
    \"to_currency\": \"JPY\"
  }'

# 현재 환율 조회
curl -X GET \"http://localhost:8000/api/v1/llm/exchange-rates?currency_codes=USD,JPY,EUR\"

# 과거 환율 조회
curl -X GET \"http://localhost:8000/api/v1/llm/exchange-rates/historical?date=20250701&currency_codes=USD\"
```

## 🛠️ 개발 환경

### 개발 도구 설정
```bash
# 개발용 의존성 설치
pip install -r requirements-dev.txt

# 코드 포맷팅
black app/ tests/
isort app/ tests/

# 린팅
flake8 app/ tests/
mypy app/

# 테스트 실행
pytest -v

# 테스트 커버리지
pytest --cov=app --cov-report=html
```

### 환경변수 설정
```env
# .env 파일 예시
DEBUG=True
ENVIRONMENT=development

# Amadeus API
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# OpenAI API (Phase 2)
OPENAI_API_KEY=your_openai_api_key

# 한국수출입은행 API (Phase 2)
KOREAEXIM_API_KEY=your_koreaexim_api_key

# Redis 설정
REDIS_URL=redis://localhost:6379
```

### 프로젝트 구조
```
backend/
├── app/
│   ├── api/v1/              # API 라우터
│   │   ├── flights.py       # 항공편 API
│   │   ├── regions.py       # 지역 API
│   │   ├── llm.py          # AI 분석 API
│   │   └── utils.py        # 유틸리티 API
│   ├── services/           # 비즈니스 로직
│   │   ├── amadeus_service.py
│   │   ├── llm/            # LLM 서비스
│   │   └── exchange_rate_service.py
│   ├── models/             # 데이터 모델
│   ├── config/             # 설정 관리
│   └── utils/              # 유틸리티
├── tests/                  # 테스트 코드
└── requirements*.txt       # 의존성 파일
```

## 📊 개발 로드맵

### ✅ Phase 1: 핵심 기능 (완료)
- [x] 기본 항공편 검색 API
- [x] 지역별 항공편 조회
- [x] 캐시 시스템 구축
- [x] 날짜/시즌 정보 서비스

### ✅ Phase 2: AI 분석 기능 (완료)
- [x] LLM 기반 항공편 분석
- [x] 실시간 가격 알림 시스템
- [x] 환율 변환 서비스
- [x] 고급 추천 시스템

### 🔄 Phase 3: 가격 예측 (개발 중)
- [ ] Amadeus API 기반 데이터 수집 시스템
- [ ] ML 파이프라인 구축 (scikit-learn, XGBoost)
- [ ] 시계열 특성 엔지니어링
- [ ] 예측 API 엔드포인트 구현

### 🔮 Phase 4: 확장 기능 (계획 중)
- [ ] 호텔 연동 서비스
- [ ] 렌터카 연동 서비스
- [ ] 사용자 개인화 기능
- [ ] 모바일 앱 개발

## 🤝 기여하기

### 기여 방법
1. **Fork** 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **브랜치에 Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 개발 가이드라인
- 코드 스타일: **PEP 8** 준수
- 테스트: 새로운 기능에 대한 테스트 작성 필수
- 문서: API 변경사항 문서 업데이트
- 커밋: [Conventional Commits](https://www.conventionalcommits.org/) 형식 사용

### 버그 리포트 및 기능 요청
[GitHub Issues](https://github.com/WiseAirPJ/flight_recommand/issues)를 통해 버그 리포트나 기능 요청을 해주세요.

---

## 📈 성능 지표

### 현재 성능
- **응답 시간**: 평균 200ms 이하
- **캐시 적중률**: 85% 이상
- **API 가용성**: 99.9% 이상
- **동시 사용자**: 최대 1,000명 지원

### 지원 범위
- **항공편 검색**: 한국 ↔ 일본 노선
- **지역 커버리지**: 일본 6개 주요 지역
- **통화 지원**: 80+ 통화 (한국수출입은행 API 기반)
- **언어 지원**: 한국어, 영어, 일본어

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🙋‍♀️ 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 언제든지 연락주세요:

- **Email**: gucci9107@gmail.com
- **GitHub Issues**: [이슈 페이지](https://github.com/WiseAirPJ/flight_recommand/issues)
- **Documentation**: [개발자 가이드](DEVELOPMENT.md)

---

<div align="center">

**🛫 지능형 일본 항공권 분석기**


</div>
