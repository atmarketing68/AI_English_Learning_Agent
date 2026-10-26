"""Run a lightweight pilot check against a deployed AGEN API.

Required: PILOT_BASE_URL
Optional: PILOT_EMAIL, PILOT_PASSWORD, PILOT_FULL_NAME, PILOT_DISPLAY_NAME
"""
import os
import sys
import time

import httpx


BASE_URL = os.environ.get("PILOT_BASE_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.environ.get("PILOT_EMAIL")
PASSWORD = os.environ.get("PILOT_PASSWORD")


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        print("PASS health")

        if not EMAIL or not PASSWORD:
            print("PASS infrastructure pilot; auth flow skipped (set PILOT_EMAIL/PILOT_PASSWORD to run it)")
            return 0

        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "full_name": os.environ.get("PILOT_FULL_NAME", "AGEN Pilot"),
                "display_name": os.environ.get("PILOT_DISPLAY_NAME", "Pilot"),
            },
        )
        if registration.status_code not in (201, 400):
            registration.raise_for_status()

        login = client.post(
            "/api/v1/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
        )
        login.raise_for_status()
        token = login.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        print("PASS authentication")

        before = client.get("/api/v1/analytics/overview")
        before.raise_for_status()
        baseline = before.json()

        job_response = client.post(
            "/api/v1/lessons/generate",
            json={"skill": "vocabulary", "topic": "Daily Routines", "background": True},
        )
        if job_response.status_code != 202:
            print(f"FAIL background generation: {job_response.status_code} {job_response.text}")
            return 1

        job = job_response.json()
        print(f"PASS job accepted trace_id={job['trace_id']}")
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            status = client.get(f"/api/v1/lessons/generation-jobs/{job['job_id']}")
            status.raise_for_status()
            payload = status.json()
            if payload["status"] == "succeeded":
                lesson_id = payload["result"]["lesson_id"]
                print(f"PASS lesson generated: {lesson_id}")
                break
            if payload["status"] == "failed":
                print(f"FAIL lesson generation: {payload.get('error')}")
                return 1
            time.sleep(2)

        print("FAIL lesson generation timed out")
        return 1

        lesson = client.get(f"/api/v1/lessons/{lesson_id}")
        lesson.raise_for_status()
        for exercise in lesson.json()["exercises"]:
            content = exercise["content"]
            if exercise["type"] == "multiple_choice":
                answer = content["correct_answer"]
            elif exercise["type"] == "fill_blank":
                answer = content["blank_word"]
            else:
                answer = "viewed"
            submitted = client.post(
                f"/api/v1/lessons/{lesson_id}/submit-exercise",
                json={"exercise_id": exercise["id"], "answer": answer},
            )
            submitted.raise_for_status()

        finished = client.post(f"/api/v1/lessons/{lesson_id}/finish")
        finished.raise_for_status()
        after = client.get("/api/v1/analytics/overview")
        after.raise_for_status()
        current = after.json()
        print(
            "OUTCOME lessons_delta={} xp_delta={} score={} skill_score_delta={}".format(
                current["total_lessons_completed"] - baseline["total_lessons_completed"],
                current["total_xp"] - baseline["total_xp"],
                finished.json()["score"],
                current["skill_scores"]["vocabulary"] - baseline["skill_scores"]["vocabulary"],
            )
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
