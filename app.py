
from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
from typing import List, Dict
import heapq

app = Flask(__name__)

@dataclass
class Job:
    id: str
    deadline: int
    profit: int
    
    def _lt_(self, other):
        return self.profit > other.profit

class DisjointSet:
    def _init_(self):
        self.parent = {}
        self.rank = {}
    
    def initialize(self, max_slot: int):
        for i in range(max_slot + 1):
            self.parent[i] = i
            self.rank[i] = 0
    
    def find(self, slot: int) -> int:
        if self.parent[slot] != slot:
            self.parent[slot] = self.find(self.parent[slot])
        return self.parent[slot]
    
    def union(self, slot1: int, slot2: int):
        root1 = self.find(slot1)
        root2 = self.find(slot2)
        
        if root1 != root2:
            if self.rank[root1] < self.rank[root2]:
                root1, root2 = root2, root1
            self.parent[root2] = root1
            if self.rank[root1] == self.rank[root2]:
                self.rank[root1] += 1
    
    def find_slot(self, deadline: int) -> int:
        slot = self.find(deadline)
        if slot > 0:
            self.union(slot, slot - 1)
        return slot

class JobScheduler:
    def _init_(self):
        self.reset()
    
    def reset(self):
        self.time_slots = DisjointSet()
        self.schedule = {}
        self.max_deadline = 0
    
    def schedule_jobs(self, jobs: List[Job]) -> Dict:
        self.reset()
        job_heap = []
        for job in jobs:
            heapq.heappush(job_heap, job)
            self.max_deadline = max(self.max_deadline, job.deadline)
        
        self.time_slots.initialize(self.max_deadline)
        
        scheduled_jobs = []
        missed_jobs = []
        
        while job_heap:
            job = heapq.heappop(job_heap)
            slot = self.time_slots.find_slot(job.deadline)
            
            if slot > 0:
                scheduled_jobs.append({
                    "slot": slot,
                    "job": {
                        "id": job.id,
                        "deadline": job.deadline,
                        "profit": job.profit
                    }
                })
                self.schedule[slot] = job
            else:
                missed_jobs.append({
                    "id": job.id,
                    "deadline": job.deadline,
                    "profit": job.profit
                })
        
        return {
            "schedule": sorted(scheduled_jobs, key=lambda x: x["slot"]),
            "missed_jobs": missed_jobs,
            "stats": self._calculate_stats(scheduled_jobs, missed_jobs)
        }
    
    def _calculate_stats(self, scheduled_jobs, missed_jobs):
        total_profit = sum(job["job"]["profit"] for job in scheduled_jobs)
        utilization = len(scheduled_jobs) / self.max_deadline * 100 if self.max_deadline > 0 else 0
        
        return {
            "total_profit": total_profit,
            "utilization_rate": round(utilization, 2),
            "scheduled_jobs": len(scheduled_jobs),
            "missed_jobs": len(missed_jobs),
            "max_deadline": self.max_deadline
        }

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    try:
        data = request.json
        jobs = [Job(
            id=job['id'],
            deadline=int(job['deadline']),
            profit=int(job['profit'])
        ) for job in data['jobs']]
        
        scheduler = JobScheduler()
        result = scheduler.schedule_jobs(jobs)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Scheduler</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-2xl font-bold mb-6">Job Scheduler</h1>
        
        <!-- Input Form -->
        <div class="bg-white p-6 rounded-lg shadow-md mb-6">
            <h2 class="text-xl mb-4">Add Job</h2>
            <form id="jobForm" class="space-y-4">
                <div class="grid grid-cols-3 gap-4">
                    <input type="text" id="jobId" placeholder="Job ID" class="border p-2 rounded" required>
                    <input type="number" id="deadline" placeholder="Deadline" class="border p-2 rounded" required>
                    <input type="number" id="profit" placeholder="Profit" class="border p-2 rounded" required>
                </div>
                <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Add Job</button>
            </form>
        </div>

        <!-- Job List -->
        <div class="bg-white p-6 rounded-lg shadow-md mb-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl">Job List</h2>
                <button id="scheduleBtn" class="bg-green-500 text-white px-4 py-2 rounded">Schedule Jobs</button>
            </div>
            <table class="w-full">
                <thead>
                    <tr class="bg-gray-50">
                        <th class="p-2 text-left">Job ID</th>
                        <th class="p-2 text-left">Deadline</th>
                        <th class="p-2 text-left">Profit</th>
                        <th class="p-2 text-left">Actions</th>
                    </tr>
                </thead>
                <tbody id="jobList"></tbody>
            </table>
        </div>

        <!-- Results -->
        <div id="results" class="bg-white p-6 rounded-lg shadow-md hidden">
            <h2 class="text-xl mb-4">Results</h2>
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-blue-50 p-4 rounded">
                    <h3 class="font-semibold">Total Profit</h3>
                    <p id="totalProfit" class="text-2xl"></p>
                </div>
                <div class="bg-green-50 p-4 rounded">
                    <h3 class="font-semibold">Utilization Rate</h3>
                    <p id="utilizationRate" class="text-2xl"></p>
                </div>
            </div>
            <div class="mb-6">
                <h3 class="font-semibold mb-2">Scheduled Jobs</h3>
                <table class="w-full">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="p-2 text-left">Time Slot</th>
                            <th class="p-2 text-left">Job ID</th>
                            <th class="p-2 text-left">Profit</th>
                        </tr>
                    </thead>
                    <tbody id="scheduleList"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let jobs = [];

        document.getElementById('jobForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const job = {
                id: document.getElementById('jobId').value,
                deadline: parseInt(document.getElementById('deadline').value),
                profit: parseInt(document.getElementById('profit').value)
            };
            jobs.push(job);
            updateJobList();
            this.reset();
        });

        function updateJobList() {
            const jobList = document.getElementById('jobList');
            jobList.innerHTML = jobs.map((job, index) => `
                <tr>
                    <td class="p-2">${job.id}</td>
                    <td class="p-2">${job.deadline}</td>
                    <td class="p-2">$${job.profit}</td>
                    <td class="p-2">
                        <button onclick="removeJob(${index})" class="text-red-500">Remove</button>
                    </td>
                </tr>
            `).join('');
        }

        function removeJob(index) {
            jobs.splice(index, 1);
            updateJobList();
        }

        document.getElementById('scheduleBtn').addEventListener('click', async function() {
            if (jobs.length === 0) {
                alert('Please add some jobs first!');
                return;
            }

            const response = await fetch('/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jobs })
            });

            const result = await response.json();
            if (result.error) {
                alert(result.error);
                return;
            }

            displayResults(result);
        });

        function displayResults(result) {
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('totalProfit').textContent = $${result.stats.total_profit};
            document.getElementById('utilizationRate').textContent = ${result.stats.utilization_rate}%;

            const scheduleList = document.getElementById('scheduleList');
            scheduleList.innerHTML = result.schedule.map(item => `
                <tr>
                    <td class="p-2">${item.slot}</td>
                    <td class="p-2">${item.job.id}</td>
                    <td class="p-2">$${item.job.profit}</td>
                </tr>
            `).join('');
        }
    </script>
</body>
</html>
"""

# Create templates directory and save HTML
import os
if not os.path.exists('templates'):
    os.makedirs('templates')
    
with open('templates/index.html', 'w') as f:
    f.write(HTML_TEMPLATE)

if __name__ == '_main_':
    app.run(debug=True)