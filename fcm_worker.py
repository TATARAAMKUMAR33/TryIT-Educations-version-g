import os, requests, json
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}

# NOTE: Replace this with your actual Firebase Server Key later
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', 'YOUR_FCM_SERVER_KEY_HERE')
FCM_URL = 'https://fcm.googleapis.com/fcm/send'

def send_push_to_all(title, body, target_email=None):
    print(f"🚀 Preparing to send push notification: {title}")
    
    # 1. Fetch device tokens
    query = f'{u}/rest/v1/device_tokens?select=*'
    if target_email:
        query += f'&user_email=eq.{target_email}'
    
    res = requests.get(query, headers=h).json()
    
    if not res:
        print("❌ No device tokens found.")
        return

    tokens = [row['fcm_token'] for row in res]
    print(f"✅ Found {len(tokens)} devices. Sending...")

    # 2. Send to FCM (Legacy API for simplicity)
    headers = {
        'Authorization': f'key={FCM_SERVER_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'registration_ids': tokens,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default'
        },
        'priority': 'high'
    }

    response = requests.post(FCM_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ FCM Push Sent Successfully!")
        print(response.json())
    else:
        print(f"❌ FCM Error: {response.status_code} - {response.text}")

# Test it out
if __name__ == "__main__":
    # This will broadcast to everyone (You can change target_email for specific users)
    send_push_to_all(
        title="🚨 TryIT Alert", 
        body="A new exam has been scheduled. Check your dashboard!"
    )
