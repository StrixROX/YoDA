from art import text2art

def greet(heading, subHeading):
    banner = text2art(heading, "sub-zero") if heading else None
    bannerWidth = banner.index("\n") if heading else None

    greeting = "--- Welcome, you are! ---"
    paddedGreeting = f"{greeting:^{bannerWidth}}" if heading else greeting

    if banner:
        print(banner)

    if paddedGreeting:
        print(paddedGreeting + "\n")
