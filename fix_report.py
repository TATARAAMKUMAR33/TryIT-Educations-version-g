content = open('hourly_report.py', encoding='utf-8').read()

# Fix SambaNova model check
content = content.replace('gemma-4-31B-it', 'gemma-4-31B-it')

# Fix NVIDIA model check - old model returns 410
content = content.replace(
    'meta/llama-3.2-90b-vision-instruct',
    'nvidia/nemotron-3-ultra-550b-a55b'
)

# Fix v3/v5 count to v7
content = content.replace('tryit_v5', 'tryit_v7')
content = content.replace('tryit_v3', 'tryit_v7')
content = content.replace('v5 engine (new)', 'v7 engine (new)')
content = content.replace('v3 engine (old)', 'v6 engine (prev)')

open('hourly_report.py', 'w', encoding='utf-8').write(content)
print('Report fixed')
