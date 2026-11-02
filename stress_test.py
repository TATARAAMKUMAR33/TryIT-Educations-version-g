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

# The URL we are stress testing (e.g., exam submissions)
URL = f'{u}/rest/v1/exam_submissions'

async def simulate_user(session, user_id):
    # Simulate a student submitting an exam
    payload = {
        "student_email": f"stress_test_{user_id}@tryit.com",
        "exam_name": "Stress Test Exam",
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
    print("🚀 Starting Stress Test: 1,000 Concurrent Users...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [simulate_user(session, i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    success = results.count(201) + results.count(204)
    failed = len(results) - success
    
    print(f"✅ Success: {success} / 1000")
    print(f"❌ Failed: {failed} / 1000")
    print(f"⏱️ Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
