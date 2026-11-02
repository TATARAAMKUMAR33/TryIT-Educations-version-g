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

async def simulate_user(session, user_id, phase_name, semaphore):
    async with semaphore:
        payload = {
            "student_email": f"stress_{phase_name}_{user_id}@tryit.com",
            "exam_name": f"Stress Test {phase_name}",
            "score": 5,
            "total_questions": 5,
            "time_taken_seconds": 120
        }
        try:
            async with session.post(URL, headers=headers, json=payload, timeout=10) as res:
                return res.status
        except Exception as e:
            return str(e)

async def run_phase(phase_name, total_users, batch_size, chunk_size):
    print(f"\n🚀 STARTING PHASE: {phase_name} ({total_users} Users)")
    start_time = time.time()
    semaphore = asyncio.Semaphore(batch_size)
    
    success = 0
    failed = 0
    
    async with aiohttp.ClientSession() as session:
        # Process in chunks to prevent laptop RAM crash
        for i in range(0, total_users, chunk_size):
            current_chunk = min(chunk_size, total_users - i)
            tasks = [simulate_user(session, i + j, phase_name, semaphore) for j in range(current_chunk)]
            results = await asyncio.gather(*tasks)
            
            success += results.count(201) + results.count(204)
            failed += sum(1 for r in results if isinstance(r, str) or (isinstance(r, int) and r not in [201, 204]))
            
            # Small pause to prevent Cloudflare ban
            await asyncio.sleep(0.5) 

    end_time = time.time()
    time_taken = end_time - start_time
    rps = total_users / time_taken
    
    print(f"✅ Success: {success} | ❌ Failed: {failed}")
    print(f"⏱️ Time: {time_taken:.2f}s | ⚡ RPS: {rps:.2f}")
    return rps

async def main():
    phases = [
        ("1K", 1000, 200, 500),
        ("10K", 10000, 500, 2000),
        ("100K", 100000, 800, 5000),
        ("500K", 500000, 1000, 10000)
    ]
    
    for name, users, batch, chunk in phases:
        try:
            await run_phase(name, users, batch, chunk)
            print("⏳ Cooling down for 3 seconds...")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ Phase {name} crashed: {e}")

if __name__ == "__main__":
    print("⚠️ WARNING: This will push your laptop and Supabase to the absolute limit.")
    asyncio.run(main())
