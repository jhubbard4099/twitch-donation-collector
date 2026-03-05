def findSubAmount(tier):
    if tier == "1000":
        return 6.00
    elif tier == "2000":
        return 10.00
    elif tier == "3000":
        return 25.00
    else:
        return 0
    
def findBitAmount(bits):
    return bits / 100.00

def main() -> None:
    print(findSubAmount("2000"))
    print(findBitAmount(5))

if __name__ == "__main__":
    main()
