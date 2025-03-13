"""
Note tracker module to handle sustain functionality and timed note releases
"""
import time
import threading
from queue import Queue
import heapq

class NoteTracker:
    def __init__(self):
        # Track all active notes with their end times
        self.active_notes = {}  # {note_number: (end_time, velocity)}
        self.release_times = {}  # {note_number: release_time} - for potential early release
        self.sustain_on = True  # Default to sustain ON
        self.note_queue = []  # Priority queue for note timeouts (end_time, note_number)
        self.running = True
        self.last_active_set = set()  # Track last reported active note set
        
        # Set up timer thread to check for expired notes
        self.timer_thread = threading.Thread(target=self._process_note_timeouts)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # Queue for sending note updates
        self.update_queue = Queue()
        
    def process_message(self, msg):
        """Process a MIDI message and update active notes."""
        now = time.time()
        notes_changed = False
        
        # Handle sustain control change
        if msg.type == 'control_change' and msg.control == 72:
            old_sustain = self.sustain_on
            self.sustain_on = (msg.value == 110)  # 110 = on, 64 = off
            
            # When turning sustain off, apply any pending note releases
            if old_sustain and not self.sustain_on:
                for note, release_time in list(self.release_times.items()):
                    if note in self.active_notes:
                        # Calculate when the note will end (0.2s after release)
                        release_end = release_time + 0.2
                        # If the release end is earlier than the scheduled end
                        if release_end < self.active_notes[note][0]:
                            # Update the end time to be 0.2s after release
                            self._update_note_end_time(note, release_end)
                            notes_changed = True
                            
        # Handle note on
        elif msg.type == 'note_on' and msg.velocity > 0:
            # Calculate note end time based on velocity
            if msg.velocity > 75:
                duration = 3.0  # 3 seconds for higher velocity
            else:
                duration = 2.0  # 2 seconds for lower velocity
                
            end_time = now + duration
            # Add or update note with new end time
            self.active_notes[msg.note] = (end_time, msg.velocity)
            
            # Remove any pending release time
            if msg.note in self.release_times:
                del self.release_times[msg.note]
                
            # Add to timeout queue
            heapq.heappush(self.note_queue, (end_time, msg.note))
            notes_changed = True
            
        # Handle note off or note on with velocity 0
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in self.active_notes:
                if self.sustain_on:
                    # With sustain on, just record the release time
                    self.release_times[msg.note] = now
                    # No actual change to active notes here!
                else:
                    # Without sustain, the note will stop in 0.2 seconds
                    release_end = now + 0.2
                    
                    # If the note would end earlier due to timeout, don't change
                    if release_end < self.active_notes[msg.note][0]:
                        self._update_note_end_time(msg.note, release_end)
                        notes_changed = True
        
        # Check if the active notes set has actually changed
        current_active_set = set(self.get_active_notes())
        if current_active_set != self.last_active_set:
            self.last_active_set = current_active_set
            self.update_queue.put(list(current_active_set))
            
    def _update_note_end_time(self, note, new_end_time):
        """Update a note's end time and add to the queue."""
        if note in self.active_notes:
            velocity = self.active_notes[note][1]
            self.active_notes[note] = (new_end_time, velocity)
            heapq.heappush(self.note_queue, (new_end_time, note))
            
    def _process_note_timeouts(self):
        """Thread function to process note timeouts."""
        while self.running:
            now = time.time()
            notes_removed = False
            
            # Check for expired notes
            while self.note_queue and self.note_queue[0][0] <= now:
                end_time, note = heapq.heappop(self.note_queue)
                
                # Only process if this is actually the current end time
                if note in self.active_notes and abs(self.active_notes[note][0] - end_time) < 0.001:
                    # Remove the note
                    del self.active_notes[note]
                    if note in self.release_times:
                        del self.release_times[note]
                    notes_removed = True
                    
            if notes_removed:
                current_active_set = set(self.get_active_notes())
                if current_active_set != self.last_active_set:
                    self.last_active_set = current_active_set
                    self.update_queue.put(list(current_active_set))
                
            time.sleep(0.01)  # Short sleep to prevent high CPU usage
            
    def get_active_notes(self):
        """Get a list of currently active notes."""
        return sorted(self.active_notes.keys())
        
    def stop(self):
        """Stop the timer thread."""
        self.running = False
