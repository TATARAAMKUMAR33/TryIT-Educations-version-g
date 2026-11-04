content = open('generate_master.py', encoding='utf-8').read()

# Skip key index 1 (key 2) which is always 403
# Change split: skip index 1, use 0,2,3 for GEN and 4 for QA
old = 'GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 3]\nGEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 3]'
new = 'GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 3]\nGEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 3]\n# Key 2 (index 1) is always 403 - filtered automatically by probe'

if old in content:
    content = content.replace(old, new)
    print('Comment added OK')
else:
    print('Already fine - probe handles it automatically')
