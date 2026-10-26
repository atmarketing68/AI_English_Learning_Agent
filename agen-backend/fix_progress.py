"""
Cleanup script: remove duplicate LearnerCurriculumProgress rows,
keeping only the one with the highest best_score per (learner, curriculum_lesson).
"""
import sqlite3

conn = sqlite3.connect('agen_dev.db')
cur = conn.cursor()

# Find duplicates
cur.execute('''
    SELECT learner_id, curriculum_lesson_id, COUNT(*) as cnt
    FROM learner_curriculum_progress
    GROUP BY learner_id, curriculum_lesson_id
    HAVING cnt > 1
''')
dupes = cur.fetchall()
print(f'Duplicate groups: {len(dupes)}')

for learner_id, cl_id, cnt in dupes:
    # Keep the row with highest best_score (or most recent if tie)
    cur.execute('''
        SELECT id, best_score FROM learner_curriculum_progress
        WHERE learner_id=? AND curriculum_lesson_id=?
        ORDER BY best_score DESC, started_at DESC
    ''', (learner_id, cl_id))
    rows = cur.fetchall()
    keep_id = rows[0][0]
    delete_ids = [r[0] for r in rows[1:]]
    print(f'  Keeping {keep_id}, deleting {delete_ids}')
    cur.executemany('DELETE FROM learner_curriculum_progress WHERE id=?', [(d,) for d in delete_ids])

# Reset remaining rows to in_progress so the next attempt registers cleanly
cur.execute('''
    UPDATE learner_curriculum_progress
    SET generated_lesson_id = NULL, best_score = 0, status = 'in_progress', mastered = 0
''')
print(f'Reset {cur.rowcount} rows.')

conn.commit()
conn.close()
print('Done.')
