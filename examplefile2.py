price_list = {"콜라": 1500, "사이다": 1400, "물": 800, "커피": 2000}
wallet = 3000   # 내가 가진 돈

for name, price in price_list.items():
    # if / elif / else: 상황에 따라 다른 동작
    if price > wallet:
        print(f"{name}({price}원): 돈이 부족해요")
    elif price <= 1000:
        wallet -= price
        print(f"{name}({price}원): 저렴해서 구매! 남은 돈 {wallet}원")
    else:
        print(f"{name}({price}원): 살 수 있지만 건너뜀")

print("최종 남은 돈:", wallet)