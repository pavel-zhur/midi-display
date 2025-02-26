"""
MIDI Reader - A simple application to read MIDI input from a connected keyboard
"""
import time
import mido
from mido import Message

def list_midi_ports():
    """List all available MIDI input ports."""
    print("Available MIDI input ports:")
    for i, port_name in enumerate(mido.get_input_names()):
        print(f"  {i}: {port_name}")

def print_midi_message(msg):
    """Print a formatted MIDI message."""
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
    
    # List available MIDI input ports
    list_midi_ports()
    
    # Ask the user to select a MIDI input port
    try:
        available_ports = mido.get_input_names()
        if not available_ports:
            print("No MIDI input ports detected!")
            print("Please make sure your MIDI keyboard is connected and drivers are installed.")
            print("On Windows, you might need to install a MIDI driver like loopMIDI or rtpMIDI.")
            return
        
        port_index = int(input("\nSelect MIDI input port number: "))
        port_name = available_ports[port_index]
        
        print(f"\nOpening {port_name}...")
        with mido.open_input(port_name) as inport:
            print(f"Connected to {port_name}. Press Ctrl+C to exit.")
            print("Play some notes on your MIDI keyboard...\n")
            
            # Continuously read MIDI messages
            while True:
                for msg in inport.iter_pending():
                    print_midi_message(msg)
                time.sleep(0.01)  # Small sleep to reduce CPU usage
                
    except KeyboardInterrupt:
        print("\nExiting MIDI Reader...")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
