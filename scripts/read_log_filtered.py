try:
    with open('erie_log.txt', 'r', encoding='utf-16') as f:
        lines = f.readlines()
except:
    try:
        with open('erie_log.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        lines = []

for line in lines:
    if "FAILED" in line or "assert" in line or "Error" in line or "E   " in line:
        print(line.strip())
