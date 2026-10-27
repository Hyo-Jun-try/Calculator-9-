scores = [95, 82, 71, 64, 50]

total = 0       # 합계를 담을 변수
pass_count = 0  # 합격자 수를 셀 변수

for score in scores:
    # 1) if / elif / else: 점수에 따라 등급 결정
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    else:
        grade = "F"

    # 2) if: 조건에 맞을 때만 실행 (카운트)
    if grade != "F":
        pass_count += 1

    # 3) 누적: 매 반복마다 합계에 더하기
    total += score

    print(f"{score}점 -> {grade}")

print("평균:", total / len(scores))
print("합격자 수:", pass_count)