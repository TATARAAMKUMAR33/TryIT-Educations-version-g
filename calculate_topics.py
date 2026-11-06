import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

topics = requests.get(f'{u}/rest/v1/topics?select=topic_id,subject_id,topic_name,difficulty_range,is_visual&limit=2000', headers=h).json()

print(f'Total topics: {len(topics)}')
print()

# Calculate total questions needed
total_needed = 0
visual_topics = 0
by_tier = {}

TIER_MAP = {
    'cbse': 'T1_School', 'icse': 'T1_School', 'tn_state': 'T1_School',
    'mh_state': 'T1_School', 'ap_ts': 'T1_School', 'karnataka': 'T1_School',
    'up_state': 'T1_School', 'bihar': 'T1_School', 'wb_state': 'T1_School',
    'gujarat': 'T1_School', 'punjab': 'T1_School', 'rajasthan': 'T1_School',
    'mp_state': 'T1_School', 'kerala': 'T1_School', 'odisha': 'T1_School',
    'assam': 'T1_School', 'nep_school': 'T1_School',
    'ug_pg_entrances': 'T2_UG_Entrance', 'gate_prep': 'T3_PG_Entrance',
    'mba_cat': 'T3_PG_Entrance', 'medical_pg': 'T3_PG_Entrance',
    'research': 'T4_PhD', 'ugc_net': 'T4_PhD',
    'french': 'T5_Foreign', 'german': 'T5_Foreign', 'ielts': 'T5_Foreign',
    'international': 'T5_Foreign', 'study_abroad': 'T5_Foreign',
    'competitive': 'T6_Govt', 'ssc': 'T6_Govt', 'rrb': 'T6_Govt',
    'bank': 'T6_Govt', 'defence': 'T6_Govt', 'upsc': 'T6_Govt',
    'state_exams': 'T7_State', 'tnpsc': 'T7_State',
}

for t in topics:
    dr = t.get('difficulty_range','2-7')
    try:
        lo, hi = map(int, dr.split('-'))
    except:
        lo, hi = 2, 7
    levels = hi - lo + 1
    q_per_level = 20 if hi <= 5 else 10
    needed = levels * q_per_level
    total_needed += needed
    if t.get('is_visual'):
        visual_topics += 1

    # Tier
    sid = t.get('subject_id','')
    tier = 'T8_Professional'
    for key, val in TIER_MAP.items():
        if key in sid:
            tier = val
            break
    by_tier[tier] = by_tier.get(tier, 0) + needed

print(f'Total questions needed across all topics: {total_needed:,}')
print(f'Visual topics (need diagrams): {visual_topics}')
print(f'Non-visual topics: {len(topics)-visual_topics}')
print()
print('BY TIER (questions needed):')
for tier in sorted(by_tier.keys()):
    print(f'  {tier}: {by_tier[tier]:,} questions')
print()
print(f'At 12,000 Q/day: {total_needed//12000} days to complete')
print(f'At 3,000 Q/run:  {total_needed//3000} runs to complete')
