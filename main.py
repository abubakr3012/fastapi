import qrcode

data = input("Enter your text or link: ")

qr = qrcode.make(data)

qr.save("qr.png")

print("QR code created successfully!")
print("Follow me on Instagram")
print("Develop_with_khuzi")

qr.show()

# import secrets
# secret_key = secrets.token_hex(32)
# print(secret_key)