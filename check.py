content = open('generate_master.py', encoding='utf-8').read()
print(f'File size: {len(content)} chars')

# Check if groq_rate_wait exists
if 'groq_rate_wait' in content:
    print('groq_rate_wait EXISTS')
else:
    print('groq_rate_wait MISSING')

# Check Gemini probe
if 'generativelanguage.googleapis.com' in content:
    print('Gemini REST probe EXISTS')
else:
    print('Gemini REST probe MISSING')

# Check call site
if 'groq_rate_wait()' in content:
    print('groq_rate_wait() CALLED')
else:
    print('groq_rate_wait() NOT CALLED')
