def calc(a, b):
    x = 0
    if a <= 0:
        return x
    if b <= 0:
        return x
    if a > b:
        x = a - b
    else:
        x = b - a
    return x