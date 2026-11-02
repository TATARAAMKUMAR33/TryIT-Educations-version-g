import asyncio
import aiohttp
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
headers = {
    'apikey': k, 
    'Authorization': f'Bearer {k}', 
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

URL = f'{u}/rest/v1/exam_submissions'

async def simulate_user(session, user_id, semaphore):
    # Semaphore prevents your laptop from opening too many ports at once
    async with semaphore:
        payload = {
            "student_email": f"stress_{user_id}@tryit.com",
            "exam_name": "10K Stress Test",
            "score": random.randint(0, 5),
            "total_questions": 5,
            "time_taken_seconds": random.randint(60, 3000)
        }
        try:
            async with session.post(URL, headers=headers, json=payload) as res:
                return res.status
        except Exception as e:
            return str(e)

async def main():
    TOTAL_USERS = 10000
    BATCH_SIZE = 200 # Only 200 requests at a time to prevent laptop crash
    
    print(f"🚀 Starting Heavy Stress Test: {TOTAL_USERS} Users (Batch Size: {BATCH_SIZE})...")
    start_time = time.time()
    
    semaphore = asyncio.Semaphore(BATCH_SIZE)
    
    async with aiohttp.ClientSession() as session:
        tasks = [simulate_user(session, i, semaphore) for i in range(TOTAL_USERS)]
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    success = results.count(201) + results.count(204)
    failed = len(results) - success
    
    print(f"✅ Success: {success} / {TOTAL_USERS}")
    print(f"❌ Failed: {failed} / {TOTAL_USERS}")
    print(f"⏱️ Time taken: {end_time - start_time:.2f} seconds")
    
    # Calculate RPS
    rps = TOTAL_USERS / (end_time - start_time)
    print(f"⚡ Requests Per Second (RPS): {rps:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
