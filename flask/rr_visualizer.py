import pygame
import time
import json

# Read process data from JSON file
with open('process_data.json', 'r') as f:
    data = json.load(f)

processes = data['processes']
burst_times = data['burst_times']
arrival_times = data['arrival_times']
time_quantum = data.get('time_quantum', 2)

pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Round Robin Scheduling Visualization")

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
        pygame.draw.line(screen, text_color, (x_pos, chart_start_y + chart_height), 
                        (x_pos, chart_start_y + chart_height + 20), 2)
        num_text = font.render(str(i), True, text_color)
        screen.blit(num_text, (x_pos - 10, chart_start_y + chart_height + 25))

    # Draw processor label
    processor_label = font.render("Processor", True, text_color)
    screen.blit(processor_label, (270, 250))

    # Draw processor box
    pygame.draw.rect(screen, active_color if processing else background_color, (240, 280, 210, 100))
    pygame.draw.rect(screen, border_color, (240, 280, 210, 100), 2)
    
    if processing:
        text = font.render(f'Processing: {processing}', True, text_color)
        screen.blit(text, (270, 300))
        
        process_index = processes.index(processing)
        remaining_time = remaining_burst_times[process_index]
        info_text = font.render(f'Remaining Time: {remaining_time}', True, text_color)
        screen.blit(info_text, (270, 330))
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

    # Draw elapsed time and quantum
    time_text = font.render(f'Time: {time_elapsed}', True, text_color)
    quantum_text = font.render(f'Time Quantum: {time_quantum}', True, text_color)
    screen.blit(time_text, (600, 10))
    screen.blit(quantum_text, (600, 40))

    pygame.display.flip()

# Initialize simulation variables
running = True
clock = pygame.time.Clock()
time_elapsed = 0
queue = []
processing = None
process_times = {}
remaining_burst_times = burst_times.copy()
current_process_time = 0
processed_arrivals = set()

# Main simulation loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Add processes based on arrival time
    for i in range(len(processes)):
        if arrival_times[i] == time_elapsed and processes[i] not in processed_arrivals:
            queue.append(processes[i])
            processed_arrivals.add(processes[i])

    # Process handling
    if processing is None and queue:
        processing = queue.pop(0)
        process_index = processes.index(processing)
        if processing not in process_times:
            process_times[processing] = [time_elapsed, 0]
        current_process_time = 0

    # Process execution
    if processing:
        process_index = processes.index(processing)
        time.sleep(1)  # Simulates processing for 1 second
        time_elapsed += 1
        current_process_time += 1
        remaining_burst_times[process_index] -= 1
        process_times[processing][1] += 1

        # Check if quantum expired or process completed
        if current_process_time >= time_quantum or remaining_burst_times[process_index] <= 0:
            if remaining_burst_times[process_index] > 0:
                queue.append(processing)
            processing = None
    else:
        if not queue and all(time <= 0 for time in remaining_burst_times):
            draw(None, queue, time_elapsed, process_times)
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
        else:
            time.sleep(1)
            time_elapsed += 1

    draw(processing, queue, time_elapsed, process_times)
    clock.tick(1)

# Calculate statistics
turnaround_times = {}
waiting_times = {}

for process in processes:
    process_index = processes.index(process)
    start_time, burst_duration = process_times[process]
    finish_time = start_time + burst_duration
    turnaround_times[process] = finish_time - arrival_times[process_index]
    waiting_times[process] = turnaround_times[process] - burst_times[process_index]

# Create and save output data
output_data = {
    'gantt_chart': [(process, start, start + duration) for process, (start, duration) in process_times.items()],
    'turnaround_times': turnaround_times,
    'waiting_times': waiting_times
}

with open('output_data.json', 'w') as f:
    json.dump(output_data, f)

pygame.quit()