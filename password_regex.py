import re

def validate_password(password):
    # 비밀번호 조건 정의
    # 1. 길이 확인 (8자 이상인지)
    if len(password) < 8:
        return "비밀번호는 최소 8자 이상이어야 합니다."
        
    # 2. 영문 소문자 포함 여부 확인
    if not re.search(r"[a-z]", password):
        return "비밀번호는 최소 한 개의 영문 소문자를 포함해야 합니다."
        
    # 3. 영문 대문자 포함 여부 확인
    if not re.search(r"[A-Z]", password):
        return "비밀번호는 최소 한 개의 영문 대문자를 포함해야 합니다."
        
    # 4. 숫자 포함 여부 확인
    if not re.search(r"[0-9]", password):
        return "비밀번호는 최소 한 개의 숫자를 포함해야 합니다."
        
    # 5. 특수문자(기호) 포함 여부 확인
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "비밀번호는 최소 한 개의 특수문자(!@#$%^&*(),.?\":{}|<>)를 포함해야 합니다."
        
    # 모든 조건을 만족하면 통과
    return "비밀번호가 유효합니다."

# 사용자 입력 받기
password = input("비밀번호를 입력하세요: ")
result = validate_password(password)
print(result)
