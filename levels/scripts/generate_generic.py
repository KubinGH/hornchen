base = """
WWWWWWWWWWWWWWW2WWWWWWWWWWWWWWWW
W..............................W
W..............................W
W..............................W
W..............................W
W..............................W
W..............................W
0..............................1
W..............................W
W..............................W
W..............................W
W..............................W
W..............................W
W..............................W
W..............................W
WWWWWWWWWWWWWWW3WWWWWWWWWWWWWWWW
""".strip()

def fbin(n, zch=4): 
    return list(int(d) for d in bin(n)[2:].zfill(zch))

for i in range(1, 16):
    b = fbin(i)
    #b -> left, right, up, down
    with open("g{}.txt".format(i), "w") as file:
        text = base
        for j in range(4):
            if b[j]:
                text = text.replace(str(j), "~")
            else:
                text = text.replace(str(j), "W")        
        file.write(text)

