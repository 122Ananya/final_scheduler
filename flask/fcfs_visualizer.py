import pygame
import time
import json

# Read process data from JSON file with validation
try:
    with open('process_data.json', 'r') as f:
        data = json.load(f)

    # Ensure all data fields are present and valid
    processes = [p for p in data['processes'] if p.strip()]
    burst_times = [int(bt) for bt in data['burst_times'] if str(bt).strip().isdigit()]
    arrival_times = [int(at) for at in data['arrival_times'] if str(at).strip().isdigit()]
    priorities = data.get('priorities', [1] * len(processes))  # Default priorities if not present

    if not processes or not burst_times or not arrival_times:
        raise ValueError("Error: Processes, burst times, or arrival times contain invalid or missing values.")
    if len(processes) != len(burst_times) or len(processes) != len(arrival_times):
        raise ValueError("Error: The number of processes, burst times, and arrival times must match.")

except (json.JSONDecodeError, ValueError) as e:
    print(f"Error reading or validating process data: {e}")
    pygame.quit()
    exit()

pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Priority Non-preemptive Scheduling Visualization")

# Define colors
background_color = (255, 255, 255)
active_color = (0, 255, 0)
waiting_color = (255, 255, 0)
completed_color = (200, 200, 200)
gantt_color = (100, 100, 255)
text_color = (0, 0, 0)
border_color = (0, 0, 0)

# Define font
font = pygame.font.Font(None, 28)

# Copy of burst times to track remaining time
remaining_burst_times = burst_times[:]

# Function to draw the current time window and processes
def draw(processing, queue, time_elapsed, process_times):
    screen.fill(background_color)
    max_time = max([t[0] + t[1] for t in process_times.values()], default=10)
    time_window_size = max(max_time, 10)
    chart_width = width - 100
    unit_width = chart_width / time_window_size

    # Draw Gantt chart
    chart_start_y = 150
    chart_height = 50
    for process, (start, duration) in process_times.items():
        segment_start = start
        segment_end = start + duration
        x_start = int(segment_start * unit_width) + 50
        x_end = int(segment_end * unit_width) + 50
        pygame.draw.rect(screen, gantt_color, (x_start, chart_start_y, x_end - x_start, chart_height))
        pygame.draw.rect(screen, border_color, (x_start, chart_start_y, x_end - x_start, chart_height), 2)
        text = font.render(process, True, text_color)
        screen.blit(text, (x_start + 5, chart_start_y - 25))

    # Draw time markers
    for i in range(time_window_size + 1):
        x_pos = int(i * unit_width) + 50
        pygame.draw.line(screen, text_color, (x_pos, chart_start_y + chart_height), (x_pos, chart_start_y + chart_height + 20), 2)
        num_text = font.render(str(i), True, text_color)
        screen.blit(num_text, (x_pos - 10, chart_start_y + chart_height + 25))

    # Draw processor label
    processor_label = font.render("Processor", True, text_color)
    screen.blit(processor_label, (270, 250))
    
    pygame.draw.rect(screen, active_color if processing else background_color, (240, 280, 210, 100))
    pygame.draw.rect(screen, border_color, (240, 280, 210, 100), 2)

    # Draw processor box
    if processing:
        text = font.render(f'Processing: {processing}', True, text_color)
        screen.blit(text, (270, 300))

        # Display remaining burst time
        process_index = processes.index(processing)
        remaining_time = remaining_burst_times[process_index]
        time_text = font.render(f'Burst Time: {remaining_time}', True, text_color)
        screen.blit(time_text, (270, 330))
    else:
        text = font.render('CPU Idle', True, text_color)
        screen.blit(text, (270, 300))

    # Draw ready queue
    ready_queue_label = font.render("Ready Queue", True, text_color)
    screen.blit(ready_queue_label, (100, 400))
    
    for i, p in enumerate(queue):
        pygame.draw.rect(screen, waiting_color, (100, 430 + i * 60, 100, 50))
        text = font.render(f'{p}', True, text_color)
        screen.blit(text, (120, 430 + i * 60 + 10))

    # Draw elapsed time
    time_text = font.render(f'Time: {time_elapsed}', True, text_color)
    screen.blit(time_text, (600, 10))

    pygame.display.flip()

# Main simulation loop
running = True
clock = pygame.time.Clock()
time_elapsed = 0
queue = []
processing = None
process_times = {}
processed_arrivals = set()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Add processes based on arrival time
    for i in range(len(processes)):
        if arrival_times[i] == time_elapsed and processes[i] not in processed_arrivals:
            queue.append(processes[i])
            processed_arrivals.add(processes[i])

    # Stop the simulation once all processes have been completed and time keeps incrementing
    if len(process_times) == len(processes) and not processing and not queue:
        draw(None, queue, time_elapsed, process_times)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            draw(None, queue, time_elapsed, process_times)
            clock.tick(1)
        break  # Exit the loop when the user quits

    # Process handling when CPU becomes active
    if processing is None and queue:
        processing = queue.pop(0)
        process_index = processes.index(processing)
        process_times[processing] = [time_elapsed, burst_times[process_index]]

    draw(processing, queue, time_elapsed, process_times)

    if processing:
        process_index = processes.index(processing)
        time.sleep(1)  # Simulate processing for 1 second
        time_elapsed += 1

        # Decrement the remaining burst time
        remaining_burst_times[process_index] -= 1

        if remaining_burst_times[process_index] <= 0:
            processing = None

    else:
        if not queue:
            time.sleep(1)  # Simulate idle time
            time_elapsed += 1

    draw(processing, queue, time_elapsed, process_times)
    clock.tick(1)

# Calculate turnaround and waiting times
turnaround_times = {}
waiting_times = {}

for process in processes:
    process_index = processes.index(process)
    start_time, burst_duration = process_times[process]
    finish_time = start_time + burst_duration
    turnaround_times[process] = finish_time - arrival_times[process_index]
    waiting_times[process] = turnaround_times[process] - burst_duration

# Create output data dictionary
output_data = {
    'gantt_chart': [(process, start, start + duration) for process, (start, duration) in process_times.items()],
    'turnaround_times': turnaround_times,
    'waiting_times': waiting_times
}

# Save the output data to a JSON file
with open('output_data.json', 'w') as f:
    json.dump(output_data, f)

pygame.quit()
