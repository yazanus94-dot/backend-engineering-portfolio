"""Synthetic log-event generator shared by tests and benchmarks."""
import random


def generate_events(n, n_users=20, seed=0, duplicate_fraction=0.05):
    rng = random.Random(seed)
    event_names = ["login", "Login", "LOGIN", "click", "purchase", "logout"]
    events = []
    t = 0
    for i in range(n):
        t += rng.randint(1, 120)
        events.append({
            "user_id": rng.randint(1, n_users),
            "event": rng.choice(event_names),
            "timestamp": t,
        })
        # occasionally inject a near-duplicate (same user, same event
        # name but different case, within a couple seconds)
        if rng.random() < duplicate_fraction:
            events.append({
                "user_id": events[-1]["user_id"],
                "event": events[-1]["event"].lower(),
                "timestamp": t + rng.randint(0, 2),
            })
    return events
