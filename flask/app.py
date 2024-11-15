from flask import Flask, render_template, request, redirect, url_for, flash
import json
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        processes = request.form['process'].split(',')
        burst_times = list(map(int, request.form['burst_time'].split(',')))
        arrival_times = list(map(int, request.form['arrival_time'].split(',')))
        algorithm = request.form['algorithm']

        # Check for time quantum if Round Robin is selected
        time_quantum = None
        if algorithm == 'Round Robin':
            time_quantum = int(request.form['time_quantum'])
            if time_quantum <= 0:
                flash("Error: Time quantum must be a positive integer.")
                return redirect(url_for('index'))

        # Check for priorities if Priority algorithm is selected
        priorities = None
        if algorithm == 'Priority':
            if 'priority' not in request.form or not request.form['priority']:
                flash("Error: Priorities are required for Priority scheduling.")
                return redirect(url_for('index'))
            priorities = list(map(int, request.form['priority'].split(',')))
            if len(priorities) != len(processes):
                flash("Error: Number of priorities must match number of processes.")
                return redirect(url_for('index'))

        # Check if input lists match in length
        if len(processes) != len(burst_times) or len(processes) != len(arrival_times):
            flash("Error: The number of processes, burst times, and arrival times must match.")
            return redirect(url_for('index'))

        # Prepare data for JSON output
        data = {
            'processes': processes,
            'burst_times': burst_times,
            'arrival_times': arrival_times,
            'algorithm': algorithm
        }
        if time_quantum:
            data['time_quantum'] = time_quantum
        if priorities:
            data['priorities'] = priorities

        # Save input data to JSON file
        with open('process_data.json', 'w') as f:
            json.dump(data, f)

        # Run the appropriate scheduling algorithm script
        try:
            if algorithm == 'FCFS':
                subprocess.run(['python', 'fcfs.py'], check=True)
            elif algorithm == 'SJF':
                subprocess.run(['python', 'sjf_visualizer.py'], check=True)
            elif algorithm == 'Round Robin':
                subprocess.run(['python', 'rr_visualizer.py'], check=True)
            elif algorithm == 'Priority':
                subprocess.run(['python', 'p_visualizer.py'], check=True)

            # Load output data
            with open('output_data.json', 'r') as f:
                output_data = json.load(f)

            # Process output data to calculate results for the front end
            job_details = []
            total_turnaround_time = 0
            total_waiting_time = 0
            num_jobs = len(output_data['turnaround_times'])

            for job in output_data['turnaround_times']:
                arrival_time = arrival_times[processes.index(job)]
                burst_time = burst_times[processes.index(job)]

                gantt_entry = next((entry for entry in output_data['gantt_chart'] if entry[0] == job), None)
                if gantt_entry:
                    _, start_time, duration = gantt_entry
                    finish_time = start_time + duration

                    turnaround_time = output_data['turnaround_times'][job]
                    waiting_time = output_data['waiting_times'][job]

                    total_turnaround_time += turnaround_time
                    total_waiting_time += waiting_time

                    job_details.append((job, arrival_time, burst_time, finish_time, turnaround_time, waiting_time))

            avg_turnaround_time = total_turnaround_time / num_jobs if num_jobs else 0
            avg_waiting_time = total_waiting_time / num_jobs if num_jobs else 0

            return render_template('results.html', job_details=job_details, avg_turnaround_time=avg_turnaround_time, avg_waiting_time=avg_waiting_time)

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            flash(f"Error: {e}")
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)