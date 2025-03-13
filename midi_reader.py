"""
MIDI Reader - A simple application to read MIDI input and detect chords
"""
import time
import mido
from mido import Message
import threading
from time import time, sleep

# Tracking current notes being played
current_notes = set()
last_detected_chord = None

def detect_chord(notes):
    """
    Detect common chords based on notes being played.
    Returns chord name or None if no recognizable chord is found.
    """
    if len(notes) < 3:
        return None
        
    # Get the root-position representation by finding the lowest note
    if not notes:
        return None
        
    # Convert to pitch classes (0-11) and sort
    pitch_classes = sorted(n % 12 for n in notes)
    
    # Get unique pitch classes (remove octave duplicates)
    unique_pitches = sorted(set(pitch_classes))
    
    # Define common chord types
    chord_types = {
        # Major triads
        (0, 4, 7): "Major",
        # Minor triads
        (0, 3, 7): "Minor",
        # Diminished triads
        (0, 3, 6): "Diminished",
        # Augmented triads
        (0, 4, 8): "Augmented",
        # Dominant 7th
        (0, 4, 7, 10): "Dominant 7th",
        # Major 7th
        (0, 4, 7, 11): "Major 7th",
        # Minor 7th
        (0, 3, 7, 10): "Minor 7th",
        # Suspended 4th
        (0, 5, 7): "Sus4",
        # Suspended 2nd
        (0, 2, 7): "Sus2"
    }
    
    # Try to find a matching chord pattern
    for pattern, chord_name in chord_types.items():
        # For each potential root note
        for i in range(12):
            # Generate the chord pattern from this root
            chord = tuple(sorted((i + interval) % 12 for interval in pattern))
            
            # Check if all required notes of this chord are being played
            if all(note in pitch_classes for note in chord) and len(chord) <= len(pitch_classes):
                root_name = get_note_name(i + 12*4).replace("4", "")  # Middle octave without number
                return f"{root_name} {chord_name}"
    
    return None

def list_midi_ports():
    """List all available MIDI input and output ports."""
    print("Available MIDI input ports:")
    for i, port_name in enumerate(mido.get_input_names()):
        print(f"  {i}: {port_name}")
    print("\nAvailable MIDI output ports:")
    for i, port_name in enumerate(mido.get_output_names()):
        print(f"  {i}: {port_name}")

def print_midi_message(msg):
    """Print a formatted MIDI message and detect chords."""
    global current_notes, last_detected_chord
    
    # Handle note tracking for chord detection
    if msg.type == 'note_on' and msg.velocity > 0:
        current_notes.add(msg.note)
        
        # Try to detect chord after adding the note
        chord = detect_chord(current_notes)
        if chord and chord != last_detected_chord:
            print(f"Chord detected: {chord}")
            last_detected_chord = chord
            
    elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
        if msg.note in current_notes:
            current_notes.remove(msg.note)
            
            # If notes were released, check if chord changed
            chord = detect_chord(current_notes)
            if chord != last_detected_chord:
                if chord:
                    print(f"Chord changed to: {chord}")
                else:
                    print("No chord detected")
                last_detected_chord = chord

    # Original message printing logic
    if msg.type == 'note_on' and msg.velocity > 0:
        note_name = get_note_name(msg.note)
        velocity = msg.velocity
        print(f"Note ON:  {note_name} (note: {msg.note}, velocity: {velocity})")
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        note_name = get_note_name(msg.note)
        print(f"Note OFF: {note_name} (note: {msg.note})")
    elif msg.type == 'control_change':
        print(f"Control change: control={msg.control}, value={msg.value}")
    elif msg.type == 'clock':
        pass
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
    print("MIDI Chord Detection Application")
    print("===============================")
    
    input_ports = mido.get_input_names()
    output_ports = mido.get_output_names()
    
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
        
        with mido.open_input(input_port_name) as inport:
            print(f"Connected. Press Ctrl+C to exit.")
            print("Play some notes on your MIDI keyboard to detect chords...\n")
            
            while True:
                for msg in inport.iter_pending():
                    print_midi_message(msg)
                sleep(0.01)
                
    except KeyboardInterrupt:
        print("\nExiting MIDI Chord Detection...")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
