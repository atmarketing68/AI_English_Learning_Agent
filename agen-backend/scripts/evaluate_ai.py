import sys
import os
import time
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the app to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.agents.lesson_agent import generate_lesson

def run_eval():
    print("AGEN AI Evaluation Framework")
    print("==================================\n")

    test_cases = [
        {"skill": "vocabulary", "topic": "Technology",                      "level": "A2"},
        {"skill": "grammar",    "topic": "Past Simple vs Present Perfect",  "level": "A2"},
        {"skill": "reading",    "topic": "A review of a new movie",         "level": "A2"},
    ]

    total_time = 0
    passed = 0

    for idx, tc in enumerate(test_cases):
        print(f"[{idx+1}] Skill='{tc['skill']}', Topic='{tc['topic']}'")
        start_time = time.time()

        try:
            # generate_lesson is sync -> call directly, no await
            result = generate_lesson(
                skill=tc["skill"],
                level=tc["level"],
                topic=tc["topic"],
            )
            latency = time.time() - start_time
            total_time += latency

            # Assertions
            exercises = result.get("exercises", [])
            assert isinstance(exercises, list), "Result should contain a list of exercises"
            assert len(exercises) >= 3, f"Should generate >= 3 exercises, got {len(exercises)}"
            assert "type" in exercises[0], "First exercise should have a 'type' field"

            print(f"   PASS ({latency:.2f}s) - {len(exercises)} exercises - Title: {result.get('title','N/A')}")
            passed += 1

        except Exception as e:
            latency = time.time() - start_time
            print(f"   FAIL ({latency:.2f}s) - Error: {str(e)}")

    avg = total_time / len(test_cases) if test_cases else 0
    print("\n==================================")
    print(f"Results : {passed}/{len(test_cases)} passed")
    print(f"Avg Latency: {avg:.2f}s")

    if passed == len(test_cases):
        print("AI Evaluation Framework PASSED!")
    else:
        print("AI Evaluation Framework had failures!")
        sys.exit(1)

if __name__ == "__main__":
    run_eval()
