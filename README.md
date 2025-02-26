# MIDI Display

A Python application to read and display MIDI data from a connected keyboard.

## Setup Instructions

### 1. Install Python

If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### 2. Install Required Packages

Run the following command in your terminal:

```bash
pip install -r requirements.txt
```

### 3. Setting up MIDI Drivers (Windows)

Windows doesn't have built-in MIDI drivers like macOS and Linux. You have a few options:

#### Option A: loopMIDI (Recommended for Windows)
1. Download and install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
2. Open loopMIDI and create a virtual MIDI port
3. In your MIDI keyboard software, route MIDI output to the loopMIDI port

#### Option B: rtpMIDI (For network MIDI)
1. Download and install [rtpMIDI](https://www.tobias-erichsen.de/software/rtpmidi.html)
2. Configure it to connect to your MIDI device

### 4. Running the Application

Run the following command:

```bash
python midi_reader.py
```

Select the appropriate MIDI input port when prompted, and start playing your MIDI keyboard.

## Troubleshooting

If no MIDI devices are detected:
1. Make sure your MIDI keyboard is connected and powered on
2. Verify that the appropriate drivers are installed
3. For USB MIDI keyboards, try a different USB port
4. Check if your keyboard requires specific drivers from the manufacturer

## Next Steps

- Visualize the MIDI data graphically
- Record and save MIDI performances
- Add effects or transformations to the MIDI data
