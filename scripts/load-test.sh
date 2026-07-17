#!/bin/bash
echo "Running load test against sample-app..."
echo "Target: http://localhost:8001"
echo "Duration: 60 seconds"
echo "Workers: 10"
echo ""

if command -v locust &> /dev/null; then
    locust -f /dev/stdin <<EOF
from locust import HttpUser, task, between
class SampleAppUser(HttpUser):
    wait_time = between(0.1, 0.5)
    @task
    def get_data(self):
        self.client.get("/api/data")
EOF
else
    echo "Installing locust..."
    pip install locust -q
    echo "Run: locust -f load_test.py --headless -u 10 -r 2 --run-time 60s"
fi
