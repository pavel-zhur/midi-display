"""
Enhanced chord detection module with support for extended chords and slash chords
"""

class ChordDetector:
    def __init__(self):
        # Define constants for chord recognition
        self._define_chord_patterns()
        
    def _define_chord_patterns(self):
        """Define patterns for chord recognition."""
        # Triads
        self.triad_types = {
            (0, 4, 7): "Major",
            (0, 3, 7): "Minor",
            (0, 3, 6): "Diminished",
            (0, 4, 8): "Augmented",
            (0, 5, 7): "Sus4",
            (0, 2, 7): "Sus2",
        }
        
        # Seventh chords
        self.seventh_types = {
            (0, 4, 7, 10): "7",               # Dominant 7th
            (0, 4, 7, 11): "Maj7",            # Major 7th
            (0, 3, 7, 10): "m7",              # Minor 7th
            (0, 3, 6, 10): "m7b5",            # Half-diminished
            (0, 3, 6, 9): "dim7",             # Diminished 7th
            (0, 3, 7, 11): "mMaj7",           # Minor-Major 7th
            (0, 4, 8, 11): "Aug7",            # Augmented Major 7th
            (0, 4, 8, 10): "7#5",             # Augmented 7th
            (0, 4, 6, 10): "7b5",             # Dominant 7th flat 5
            (0, 5, 7, 10): "7sus4",           # Dominant 7th sus4
        }

        # Ninth chords
        self.ninth_types = {
            (0, 4, 7, 10, 14): "9",           # Dominant 9th
            (0, 4, 7, 11, 14): "Maj9",        # Major 9th
            (0, 3, 7, 10, 14): "m9",          # Minor 9th
            (0, 4, 7, 10, 13): "7b9",         # Dominant 7th flat 9
            (0, 4, 7, 10, 15): "7#9",         # Dominant 7th sharp 9
        }

        # Extended and altered chords
        self.extended_types = {
            (0, 4, 7, 10, 14, 17): "11",      # Dominant 11th
            (0, 4, 7, 11, 14, 17): "Maj11",   # Major 11th
            (0, 3, 7, 10, 14, 17): "m11",     # Minor 11th
            (0, 4, 7, 10, 14, 17, 21): "13",  # Dominant 13th
            (0, 4, 7, 11, 14, 17, 21): "Maj13", # Major 13th
            (0, 3, 7, 10, 14, 17, 21): "m13", # Minor 13th
        }
        
        # Added note chords
        self.added_note_types = {
            (0, 4, 7, 14): "add9",           # Major add 9
            (0, 3, 7, 14): "madd9",          # Minor add 9
            (0, 4, 7, 17): "add11",          # Major add 11
            (0, 3, 7, 17): "madd11",         # Minor add 11
            (0, 4, 7, 21): "add13",          # Major add 13
            (0, 3, 7, 21): "madd13",         # Minor add 13
        }
        
        # 6th chords
        self.sixth_types = {
            (0, 4, 7, 9): "6",               # Major 6th
            (0, 3, 7, 9): "m6",              # Minor 6th
            (0, 4, 7, 9, 14): "6/9",         # 6/9 chord
        }
        
    def get_note_name(self, note_number, with_octave=False):
        """
        Convert MIDI note number to note name.
        If with_octave is True, includes octave number (e.g., C4, F#5).
        Otherwise, returns just the note name (e.g., C, F#).
        """
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[note_number % 12]
        if with_octave:
            octave = (note_number // 12) - 1
            return f"{note}{octave}"
        return note
        
    def detect_chord(self, notes):
        """
        Detect common chords based on notes being played.
        Returns chord name or None if no recognizable chord is found.
        Also detects slash chords where bass note is different from root.
        """
        if not notes or len(notes) < 3:
            return None
        
        # Get bass note (lowest note)
        bass_note = min(notes)
        bass_pitch_class = bass_note % 12
        
        # Convert to pitch classes (0-11) and sort
        pitch_classes = sorted(set(n % 12 for n in notes))
        
        if len(pitch_classes) < 3:  # Need at least 3 unique pitch classes
            return None
            
        # Try to identify the chord
        chord_name = self._identify_chord(pitch_classes)
        
        # If no chord recognized, return None
        if chord_name is None:
            return None
        
        # Extract the root note from the chord name
        root = chord_name.split()[0]
        root_pc = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 
                   'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}[root]
        
        # Check if the bass note is different from the root
        if bass_pitch_class != root_pc:
            bass_name = self.get_note_name(bass_pitch_class)
            chord_name = f"{chord_name}/{bass_name}"
        
        return chord_name
        
    def _identify_chord(self, pitch_classes):
        """Identify the chord from the given pitch classes."""
        # Try every possible root
        for root in range(12):
            # Normalize pitch classes to this root
            normalized_pcs = sorted([(pc - root) % 12 for pc in pitch_classes])
            
            # Try to match extended chords first (largest patterns first)
            for pattern, name in self.extended_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
                    
            # Try ninth chords
            for pattern, name in self.ninth_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
            
            # Try seventh chords
            for pattern, name in self.seventh_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
                    
            # Try sixth chords
            for pattern, name in self.sixth_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
            
            # Try added note chords
            for pattern, name in self.added_note_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
            
            # Try triads (smallest patterns last)
            for pattern, name in self.triad_types.items():
                if self._is_matching_pattern(normalized_pcs, pattern):
                    return f"{self.get_note_name(root)} {name}"
        
        return None
    
    def _is_matching_pattern(self, normalized_pcs, pattern):
        """Check if the normalized pitch classes match the pattern."""
        # All notes in the pattern must be present
        if not all(p in normalized_pcs for p in pattern):
            return False
            
        # For more reliable detection, check that we don't have too many extra notes
        # We'll allow up to 2 extra notes beyond the pattern
        return len(normalized_pcs) <= len(pattern) + 2
