import re

encryption_key = "3000176000856006061501533003690027800375"


def hex_xor(s, xor_str):
    decrypted = ""
    for i in range(0, len(s), 2):
        char1 = int(s[i:i + 2], 16)
        char2 = int(xor_str[i:i + 2], 16)
        xored = hex(char1 ^ char2)[2:]
        if len(xored) == 1:
            xored = "0" + xored
        decrypted += xored
    return decrypted


def unbox(s):
    _map = [15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27, 22, 23, 25, 13, 6, 11, 39, 18, 20, 8, 14, 21, 32, 26,
            2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36]
    unboxed = [''] * len(_map)
    for i, char in enumerate(s):
        for j in range(len(_map)):
            if _map[j] == i + 1:
                unboxed[j] = char
    return ''.join(unboxed)


def get_acw_sc__v2(script_str):
    pattern = r"(?<=arg1\=')[^']+(?=';)"
    findall = re.findall(pattern, script_str)
    encrypted_id = findall[0]

    decrypted_id = unbox(encrypted_id)
    decrypted_value = hex_xor(decrypted_id, encryption_key)
    return decrypted_value
