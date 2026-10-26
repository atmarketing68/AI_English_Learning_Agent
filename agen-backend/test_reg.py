import requests
import sqlite3

url = 'http://localhost:8000/api/v1/auth/register'
data = {
    'email': 'test@example.com',
    'password': 'Password123!',
    'full_name': 'Test User',
    'display_name': 'Tester'
}

print('=== Test Registration ===')
r1 = requests.post(url, json=data)
print(f'R1: {r1.status_code} {r1.text}')

r2 = requests.post(url, json=data)
print(f'R2: {r2.status_code} {r2.text}')

print('=== Cleaning up ===')
conn = sqlite3.connect('agen_dev.db')
conn.execute("DELETE FROM users WHERE email='test@example.com'")
conn.commit()
conn.close()
print('Done.')
