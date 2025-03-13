"""
MIDI Reader - A simple application to read MIDI input and detect chords
with sustain functionality and rhythm detection
"""
import time
import mido
from mido import Message
import threading
from time import time, sleep
from logic.note_tracker import NoteTracker
from logic.chord_detector import ChordDetector
from logic.rhythm_detector import RhythmDetector

# Create detector instances
chord_detector = ChordDetector()

def get_note_name(note_number):
    """Convert MIDI note number to note name (e.g., C4, F#5)."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"

def list_midi_ports():
    """List all available MIDI input and output ports."""
    print("Available MIDI input ports:")
    for i, port_name in enumerate(mido.get_input_names()):
        print(f"  {i}: {port_name}")
    print("\nAvailable MIDI output ports:")
    for i, port_name in enumerate(mido.get_output_names()):
        print(f"  {i}: {port_name}")

def print_active_notes(active_notes):
    """Print a formatted line with chord and active notes."""
    # Format: (chord, exactly 20 chars) (3 spaces) (space-separated notes)
    
    # Get chord if any using the enhanced chord detector
    chord = chord_detector.detect_chord(active_notes) if active_notes else None
    chord_str = chord if chord else "No chord"
    
    # Format chord part to exactly 20 characters
    chord_part = chord_str[:20].ljust(20)
    
    # Format notes part
    note_names = [get_note_name(note) for note in active_notes]
    notes_part = " ".join(note_names) if note_names else "None"
    
    # Combine into final output
    print(f"{chord_part}   {notes_part}")

def print_midi_message(msg, note_tracker, rhythm_detector):
    """Print MIDI message info and update trackers."""
    if msg.type == 'note_on' and msg.velocity > 0:
        note_name = get_note_name(msg.note)
        velocity = msg.velocity
        #print(f"Note ON:  {note_name} (note: {msg.note}, velocity: {velocity})")
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        note_name = get_note_name(msg.note)
        #print(f"Note OFF: {note_name} (note: {msg.note})")
    elif msg.type == 'control_change':
        if msg.control == 72:
            status = "ON" if msg.value == 110 else "OFF"
            print(f"Sustain {status} (control={msg.control}, value={msg.value})")
        else:
            print(f"Control change: control={msg.control}, value={msg.value}")
    elif msg.type == 'clock':
        pass
    else:
        print(f"Other MIDI message: {msg}")
    
    # Update trackers with the message
    note_tracker.process_message(msg)
    rhythm_detector.process_message(msg)

def main():
    """Main function to run the MIDI reader application."""
    print("MIDI Reader with Chord Detection and Rhythm Detection")
    print("==================================================")
    
    input_ports = mido.get_input_names()
    
    if not input_ports:
        print("No MIDI input ports detected!")
        return
        
    # Automatically select if only one device
    if len(input_ports) == 1:
        input_port_name = input_ports[0]
        print(f"Automatically selected input port: {input_port_name}")
    else:
        list_midi_ports()
        port_index = int(input("\nSelect MIDI input port number: "))
        input_port_name = input_ports[port_index]
    
    try:
        print(f"\nOpening {input_port_name} for input...")
        note_tracker = NoteTracker()
        rhythm_detector = RhythmDetector()
        
        # Thread to monitor for note tracker updates
        def process_updates():
            while True:
                active_notes = note_tracker.update_queue.get()
                print_active_notes(active_notes)
                note_tracker.update_queue.task_done()
        
        update_thread = threading.Thread(target=process_updates)
        update_thread.daemon = True
        update_thread.start()
        
        with mido.open_input(input_port_name) as inport:
            print(f"Connected. Press Ctrl+C to exit.")
            print("Play some notes on your MIDI keyboard...\n")
            
            while True:
                for msg in inport.iter_pending():
                    print_midi_message(msg, note_tracker, rhythm_detector)
                sleep(0.01)
                
    except KeyboardInterrupt:
        print("\nExiting MIDI Reader...")
        if 'note_tracker' in locals():
            note_tracker.stop()
        if 'rhythm_detector' in locals():
            rhythm_detector.stop()
    except Exception as e:
        print(f"\nError: {e}")
        if 'note_tracker' in locals():
            note_tracker.stop()
        if 'rhythm_detector' in locals():
            rhythm_detector.stop()

if __name__ == "__main__":
    main()
