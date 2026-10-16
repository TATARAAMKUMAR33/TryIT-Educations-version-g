#!/bin/bash
cd /workspaces/TryIT-Educations-version-g
LOG="generation_$(date +%Y%m%d).log"
echo "🚀 Started: $(date)" | tee -a "$LOG"
for i in $(seq 1 200); do
    echo "─── Run #$i at $(date) ───" | tee -a "$LOG"
    python3 -u generate_master.py 2>&1 | tee -a "$LOG"
    CODE=${PIPESTATUS[0]}
    if [ $CODE -eq 0 ]; then
        echo "✅ Clean exit" | tee -a "$LOG"
        break
    fi
    echo "⚠️ Crash code=$CODE. Restart in 20s..." | tee -a "$LOG"
    sleep 20
done
echo "🏁 Done: $(date)" | tee -a "$LOG"
