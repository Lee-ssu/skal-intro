# 사용자 입력을 반복적으로 입력받아 출력하는 프로그램
def main():
    print("--- 앵무새 프로그램 시작 (종료하려면 !quit 입력) ---")
    
    # 무한히 반복해서 실행하라는 명령어
    while True:
        user_input = input("문장을 입력하세요: ") # 사용자 입력 받기
        
        # 사용자가 !quit을 입력했다면?
        if user_input == "!quit":
            print("프로그램을 종료합니다. 이용해 주셔서 감사합니다!")
            break # 반복문을 즉시 탈출(종료)합니다.
            
        # !quit이 아니라면 입력받은 문장을 그대로 출력
        print("입력하신 문장은:", user_input)
        print("-" * 30) # 구분을 위한 줄바꿈 선

if __name__ == "__main__":
    main()