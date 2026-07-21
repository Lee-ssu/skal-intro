# DAY1 종합실습 제출물

- 제출자: 울산 3반 이상수
- 작성일: 2026-07-20
- 실습 환경: PostgreSQL 17.10, DBeaver 26.1.3, `telecom`

## 파일 구성

- `울산_3반_이상수_DAY1_과제1_정규화.pdf`: 과제 1(B-1) 독립 제출용 PDF, DBeaver 환경 증빙 포함 5페이지
- `울산_3반_이상수_DAY1_과제2_단일테이블조회.pdf`: 과제 2(B-2) 독립 제출용 PDF, DBeaver 실행 증빙 포함 4페이지
- `울산_3반_이상수_DAY1_종합실습.pdf`: 최종 제출용 8페이지 보고서
- `울산_3반_이상수_DAY1_종합실습.docx`: 편집 가능한 원본 보고서
- `울산_3반_이상수_DAY1_과제.sql`: B-2 단일 테이블 조회 SQL
- `b2_result.csv`: 실제 `telecom.public.customer` 조회 결과 15건
- `telecom_erd.png`: 샘플 DB의 `public` 스키마 ERD
- `normalized_erd.png`: B-1 주문 내역의 최종 3NF ERD

## 검증 결과

- `public.customer`: 500건
- `public.subscription`: 800건
- B-2 조건 일치: 183건
- 제출 쿼리 출력: 가입일 오름차순 15건
- DOCX 접근성 검사: 경고 0건
- 최종 PDF: 태그 포함, 8페이지
- 과제별 PDF: 과제 1 전체 5페이지 및 과제 2 전체 4페이지 렌더링 검수 완료

> B-2 쿼리는 샘플 데이터가 들어 있는 `telecom.public.customer`를 대상으로 실행했다. 이전 DDL/DML 연습 객체는 `lab` 스키마에 분리했다.
