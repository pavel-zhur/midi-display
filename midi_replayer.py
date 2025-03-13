"""
MIDI Reader - A simple application to read MIDI input from a connected keyboard
"""
import time
import mido
from mido import Message
import threading
from queue import PriorityQueue
import heapq
from time import time, sleep

class Config:
    def __init__(self):
        self.delay_ms = 500
        self.semitone_shift = 4  # Default to major third

# Add global config
config = Config()

def get_user_config():
    """Get user configuration for delay and pitch shift."""
    print("\nPlayback Configuration")
    print("=====================")
    try:
        delay = int(input("Enter delay in milliseconds (default: 500): ") or "500")
        shift = int(input("Enter semitone shift (e.g., 4 for major third, 7 for perfect fifth): ") or "4")
        return delay, shift
    except ValueError:
        print("Invalid input, using defaults")
        return 500, 4

def list_midi_ports():
    """List all available MIDI input and output ports."""
    print("Available MIDI input ports:")
    for i, port_name in enumerate(mido.get_input_names()):
        print(f"  {i}: {port_name}")
    print("\nAvailable MIDI output ports:")
    for i, port_name in enumerate(mido.get_output_names()):
        print(f"  {i}: {port_name}")

current_notes = set()

def detect_chord(notes):
    # Simple logic to detect major/minor triads in root position:
    # returns chord name like "C Major" or "C Minor" or "Unknown chord"
    if len(notes) < 3:
        return None
    # For demonstration, let's only detect C major (C-E-G) and C minor (C-D#-G)
    # Convert to sorted list
    sorted_notes = sorted(n % 12 for n in notes)
    if {0, 4, 7}.issubset(sorted_notes):
        return "C Major"
    if {0, 3, 7}.issubset(sorted_notes):
        return "C Minor"
    return None

class NoteScheduler:
    def __init__(self, output_port):
        self.output_port = output_port
        self.schedule = []
        self.running = True
        self.thread = threading.Thread(target=self._process_schedule)
        self.thread.daemon = True
        self.thread.start()

    def schedule_note(self, msg, delay):
        play_time = time() + delay
        if msg.type == 'note_on':
            # Create a new message with shifted pitch
            shifted_msg = msg.copy(note=msg.note + config.semitone_shift)
            heapq.heappush(self.schedule, (play_time, shifted_msg))
        elif msg.type == 'note_off':
            # Need to send note_off for the shifted note
            shifted_msg = msg.copy(note=msg.note + config.semitone_shift)
            heapq.heappush(self.schedule, (play_time, shifted_msg))

    def _process_schedule(self):
        while self.running:
            now = time()
            while self.schedule and self.schedule[0][0] <= now:
                _, msg = heapq.heappop(self.schedule)
                self.output_port.send(msg)
            sleep(0.001)

    def stop(self):
        self.running = False

def print_midi_message(msg, scheduler):
    """Print a formatted MIDI message and schedule echo if needed."""
    global current_notes
    
    # Handle note tracking for chord detection
    if msg.type == 'note_on' and msg.velocity > 0:
        current_notes.add(msg.note)
    elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
        if msg.note in current_notes:
            current_notes.remove(msg.note)

    # Schedule echo for notes with configured delay
    if msg.type in ['note_on', 'note_off']:
        scheduler.schedule_note(msg, config.delay_ms / 1000.0)

    # Original message printing logic
    if msg.type == 'note_on':
        note_name = get_note_name(msg.note)
        velocity = msg.velocity
        print(f"Note ON:  {note_name} (note: {msg.note}, velocity: {velocity})")
    elif msg.type == 'note_off':
        note_name = get_note_name(msg.note)
        print(f"Note OFF: {note_name} (note: {msg.note})")
    elif msg.type == 'control_change':
        print(f"Control change: control={msg.control}, value={msg.value}")
    else:
        print(f"Other MIDI message: {msg}")

def get_note_name(note_number):
    """Convert MIDI note number to note name (e.g., C4, F#5)."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"

def main():
    """Main function to run the MIDI reader application."""
    print("MIDI Reader Application")
    print("======================")
    
    # Get user configuration
    config.delay_ms, config.semitone_shift = get_user_config()
    
    list_midi_ports()
    
    try:
        # Input port selection
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()
        
        if not input_ports or not output_ports:
            print("No MIDI ports detected!")
            return
        
        port_index = int(input("\nSelect MIDI input port number: "))
        input_port_name = input_ports[port_index]
        
        port_index = int(input("Select MIDI output port number: "))
        output_port_name = output_ports[port_index]
        
        print(f"\nOpening {input_port_name} for input and {output_port_name} for output...")
        
        with mido.open_input(input_port_name) as inport, \
             mido.open_output(output_port_name) as outport:
            
            scheduler = NoteScheduler(outport)
            print(f"Connected. Press Ctrl+C to exit.")
            print("Play some notes on your MIDI keyboard...\n")
            
            while True:
                for msg in inport.iter_pending():
                    print_midi_message(msg, scheduler)
                sleep(0.01)
                
    except KeyboardInterrupt:
        print("\nExiting MIDI Reader...")
        if 'scheduler' in locals():
            scheduler.stop()
    except Exception as e:
        print(f"\nError: {e}")
        if 'scheduler' in locals():
            scheduler.stop()

if __name__ == "__main__":
    main()
