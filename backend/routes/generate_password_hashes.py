import bcrypt

# List of plain-text passwords you want to hash
passwords = [
    "rheafer2017",
    "11210826Cpa!",
    "D-Sambitan2001",
    "dean@1995",
    "090894,bday",
    "Sabelita042901!",
    "Fransteak!19",
    "InternalAuditor08252023*",
    "audit2025*",
    "blu3@T0p",
    "oic051381",
    "Hrdepartment2022?",
    "carLstein0512*",
    "janolino_14",
    "Amanashy0w."
]

print("Generating bcrypt hashes for the provided passwords:")
print("-" * 50)

for password in passwords:
    # Encode the password to bytes before hashing
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Decode the hashed password to a string for storage
    print(f"Original: {password}")
    print(f"Hashed:   {hashed_password.decode('utf-8')}")
    print("-" * 50)

print("\nCopy these hashed passwords and update your registered.csv file.")