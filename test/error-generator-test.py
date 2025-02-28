#!/usr/bin/env python3
import argparse
import asyncio
import aiohttp
import random
import time
from datetime import datetime
from typing import List, Dict

ERROR_TYPES = [
    "INTERNAL_ERROR",
    "VALIDATION_ERROR",
    "TIMEOUT_ERROR",
    "DEPENDENCY_ERROR"
]

class ErrorGeneratorTest:
    def __init__(self, base_url: str, requests_per_second: int, duration_seconds: int):
        self.base_url = base_url.rstrip('/')
        self.requests_per_second = requests_per_second
        self.duration_seconds = duration_seconds
        self.results: Dict[str, Dict[str, int]] = {
            'success': {'count': 0},
            'error': {'count': 0}
        }

    async def make_request(self, session: aiohttp.ClientSession) -> None:
        """Make a single request to the error generator endpoint"""
        error_type = random.choice(ERROR_TYPES)
        # Randomize error rate between 0.1 and 0.9
        error_rate = random.uniform(0.1, 0.9)
        # Add random latency between 0-2000ms
        latency = random.randint(0, 2000)

        url = f"{self.base_url}/api/error-generator"
        params = {
            'errorType': error_type,
            'errorRate': str(error_rate),
            'latencyMs': str(latency)
        }

        try:
            start_time = time.time()
            async with session.get(url, params=params) as response:
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                status = response.status
                result_type = 'success' if status == 200 else 'error'
                
                self.results[result_type]['count'] += 1
                if status not in self.results[result_type]:
                    self.results[result_type][status] = 0
                self.results[result_type][status] += 1

                print(f"{datetime.now().isoformat()} | {status} | {error_type} | rate={error_rate:.2f} | latency={elapsed:.0f}ms")

        except Exception as e:
            print(f"Request failed: {str(e)}")
            self.results['error']['count'] += 1

    async def run_test(self) -> None:
        """Run the load test"""
        print(f"\nStarting error generation test:")
        print(f"Base URL: {self.base_url}")
        print(f"Duration: {self.duration_seconds} seconds")
        print(f"Rate: {self.requests_per_second} requests/second")
        print("\nTimestamp | Status | Error Type | Error Rate | Latency")
        print("-" * 70)

        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            while time.time() - start_time < self.duration_seconds:
                tasks = []
                for _ in range(self.requests_per_second):
                    task = asyncio.create_task(self.make_request(session))
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                # Wait for the next second
                next_second = (start_time + len(self.results['success']['count'] + self.results['error']['count']) // self.requests_per_second + 1)
                sleep_time = next_second - time.time()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        print("\nTest completed! Results:")
        print("-" * 40)
        print(f"Total Successful Requests: {self.results['success']['count']}")
        print(f"Total Failed Requests: {self.results['error']['count']}")
        print("\nStatus Code Distribution:")
        for result_type in ['success', 'error']:
            for status, count in self.results[result_type].items():
                if status != 'count':
                    print(f"  {status}: {count}")

def main():
    parser = argparse.ArgumentParser(description='Generate test traffic for the error generator endpoint')
    parser.add_argument('--url', default='http://localhost:8080',
                      help='Base URL of the frontend service')
    parser.add_argument('--rps', type=int, default=5,
                      help='Requests per second')
    parser.add_argument('--duration', type=int, default=60,
                      help='Test duration in seconds')
    
    args = parser.parse_args()
    
    test = ErrorGeneratorTest(args.url, args.rps, args.duration)
    asyncio.run(test.run_test())

if __name__ == '__main__':
    main()
