"""데이터베이스 연결 및 세션 관리"""
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

# SQLAlchemy 엔진 설정
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # 연결 풀 헬스 체크
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 최대 오버플로우 연결 수
    pool_recycle=3600,  # 1시간마다 연결 재활용
    connect_args={
        "connect_timeout": 10,  # 연결 타임아웃 10초
        "options": "-c timezone=Asia/Seoul",  # 타임존 설정
    },
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 베이스 클래스 (모든 모델이 상속)
Base = declarative_base()


# 데이터베이스 세션 의존성
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성

    FastAPI 의존성 주입에서 사용:
    ```python
    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()
    ```

    Yields:
        Session: SQLAlchemy 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 데이터베이스 초기화 함수
def init_db() -> None:
    """
    데이터베이스 초기화

    - 모든 테이블 생성
    - 초기 데이터 삽입 (필요시)

    주의: 운영 환경에서는 Alembic 마이그레이션 사용 권장
    """
    # 모든 모델을 임포트해야 Base.metadata에 등록됨
    # 예: from app.models import user, flight, recommendation

    Base.metadata.create_all(bind=engine)


# 데이터베이스 헬스 체크 함수
def check_db_connection() -> bool:
    """
    데이터베이스 연결 상태 확인

    Returns:
        bool: 연결 성공 여부
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return False


# PostgreSQL 특화 설정
@event.listens_for(engine, "connect")
def set_postgresql_defaults(dbapi_conn, connection_record):
    """
    PostgreSQL 연결 시 기본 설정

    - 타임존 설정
    - 문자셋 설정
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("SET timezone='Asia/Seoul'")
    cursor.execute("SET client_encoding='UTF8'")
    cursor.close()
