"""
Rhythm detection module - Detects BPM and beats from MIDI input
"""
import time
import threading
import numpy as np
from collections import deque
import math
from colorama import init, Fore, Style, Back

# Initialize colorama for colored terminal output
init()

class RhythmDetector:
    def __init__(self):
        # Store recent note onset times (timestamp when note was pressed)
        self.note_onsets = deque(maxlen=100)
        
        # Beat tracking
        self.beat_interval = None  # Time between beats in seconds
        self.last_beat_time = None
        self.confidence = 0.0      # Confidence in detected rhythm (0.0-1.0)
        self.bpm = None
        
        # Debug information
        self.last_debug_time = 0
        self.debug_interval = 1.0  # Show debug info every second
        self.potential_bpms = []   # Store potential BPM candidates
        
        # Adaptability parameters
        self.min_confidence_threshold = 0.4  # Lower threshold for easier detection
        self.min_display_threshold = 0.2    # Threshold for showing debug info
        self.adaptation_rate = 0.3   # Rate at which to adapt to new rhythm patterns
        self.detection_count = 0     # Count successful detections
        
        # Thread control
        self.running = True
        self.last_output_time = 0
        
        # Print initial message
        print(f"{Fore.CYAN}Rhythm detector initialized. Waiting for notes...{Style.RESET_ALL}")
        
        # Start beat tracking thread
        self.beat_thread = threading.Thread(target=self._beat_tracker)
        self.beat_thread.daemon = True
        self.beat_thread.start()
        
    def process_message(self, msg):
        """Process MIDI messages to detect rhythm patterns."""
        current_time = time.time()
        
        # We only care about note-on messages with velocity > 0
        if msg.type == 'note_on' and msg.velocity > 0:
            self.note_onsets.append(current_time)
            self._analyze_rhythm()
            
            # Show debug info periodically regardless of confidence
            if current_time - self.last_debug_time > self.debug_interval:
                self._show_debug_info()
                self.last_debug_time = current_time
    
    def _analyze_rhythm(self):
        """Analyze recent note onsets to detect rhythm patterns."""
        if len(self.note_onsets) < 6:  # Reduced from 8 to 6 for quicker feedback
            if len(self.note_onsets) == 1:
                print(f"{Fore.YELLOW}First note detected. Collecting rhythm data...{Style.RESET_ALL}")
            return
            
        # Calculate time intervals between consecutive notes
        intervals = [self.note_onsets[i] - self.note_onsets[i-1] 
                    for i in range(1, len(self.note_onsets))]
        
        # Filter out very long intervals (likely pauses)
        intervals = [i for i in intervals if i < 2.0]
        
        if not intervals:
            return
            
        # Find most likely beat interval using clustering
        beat_interval, confidence, candidate_bpms = self._find_beat_interval(intervals)
        self.potential_bpms = candidate_bpms
        
        if beat_interval and confidence > 0.3:  # Lower threshold for analysis
            new_bpm = round(60 / beat_interval)
            
            # Ensure BPM is in reasonable range (40-240)
            if new_bpm < 40:
                beat_interval /= 2
                new_bpm *= 2
            elif new_bpm > 240:
                beat_interval *= 2
                new_bpm /= 2
            
            # If we already have a beat interval, blend with the new one for stability
            if self.beat_interval:
                # Weighted average: Previous value with more weight for stability
                self.beat_interval = (1-self.adaptation_rate) * self.beat_interval + self.adaptation_rate * beat_interval
                self.confidence = (1-self.adaptation_rate) * self.confidence + self.adaptation_rate * confidence
                self.bpm = round(60 / self.beat_interval)
            else:
                self.beat_interval = beat_interval
                self.confidence = confidence
                self.bpm = new_bpm
                print(f"{Fore.GREEN}Initial rhythm detected: ~{self.bpm} BPM (confidence: {self.confidence:.2f}){Style.RESET_ALL}")
                
            # If this is our first detection or we lost the beat, set the last beat time
            if self.last_beat_time is None:
                self.last_beat_time = self.note_onsets[-1]
                
            # Count successful detections
            self.detection_count += 1
                
    def _find_beat_interval(self, intervals):
        """Find the most likely beat interval from the given note intervals."""
        if not intervals:
            return None, 0.0, []
            
        # Create histogram of intervals
        hist, bin_edges = np.histogram(intervals, bins=30, range=(0.1, 2.0))
        
        if np.sum(hist) == 0:
            return None, 0.0, []
            
        # Normalize histogram
        hist = hist / np.sum(hist)
        
        # Apply smoothing to the histogram
        hist_smooth = np.convolve(hist, [0.1, 0.2, 0.4, 0.2, 0.1], mode='same')
        
        # Find peaks in the histogram
        peaks = []
        for i in range(1, len(hist_smooth)-1):
            if hist_smooth[i] > hist_smooth[i-1] and hist_smooth[i] > hist_smooth[i+1] and hist_smooth[i] > 0.05:
                bin_center = (bin_edges[i] + bin_edges[i+1])/2
                peaks.append((hist_smooth[i], bin_center))
                
        if not peaks:
            return None, 0.0, []
            
        # Sort peaks by height (descending)
        peaks.sort(reverse=True)
        
        # Calculate confidence based on peak prominence
        confidence = peaks[0][0]
        if len(peaks) > 1:
            # If multiple peaks, reduce confidence
            confidence *= (1 - peaks[1][0]/peaks[0][0])
            
        # Get BPM candidates for debugging
        bpm_candidates = [(round(60/interval), height) for height, interval in peaks[:3]]
        
        # Return the highest peak as the beat interval
        beat_interval = peaks[0][1]
            
        return beat_interval, confidence, bpm_candidates
        
    def _beat_tracker(self):
        """Thread to track beats and output visualization."""
        while self.running:
            if self.beat_interval and self.last_beat_time:
                current_time = time.time()
                
                # Time since the last beat
                time_since_last_beat = current_time - self.last_beat_time
                
                # Calculate how many beats have passed and where we are in the current beat
                beats_passed = time_since_last_beat / self.beat_interval
                fraction_in_beat = beats_passed - math.floor(beats_passed)
                
                # If we're close to a beat boundary (beginning of a beat)
                if fraction_in_beat < 0.08 or fraction_in_beat > 0.92:
                    # Prevent multiple outputs for same beat
                    if current_time - self.last_output_time > self.beat_interval * 0.5:
                        # Strong confidence - show BEAT
                        if self.confidence > self.min_confidence_threshold:
                            print(f"{Fore.RED}{Back.WHITE} BEAT {Style.RESET_ALL} {Fore.CYAN}BPM ≈ {self.bpm} (confidence: {self.confidence:.2f}){Style.RESET_ALL}")
                        # Medium confidence - show weaker indication
                        elif self.confidence > self.min_display_threshold:
                            print(f"{Fore.YELLOW}beat? {Style.RESET_ALL} {Fore.CYAN}BPM ≈ {self.bpm} (confidence: {self.confidence:.2f}){Style.RESET_ALL}")
                        
                        self.last_output_time = current_time
                        
                    # Update beat time to maintain phase
                    beats_to_advance = math.floor(beats_passed)
                    if beats_to_advance > 0:
                        self.last_beat_time += beats_to_advance * self.beat_interval
                
            time.sleep(0.01)
            
    def _show_debug_info(self):
        """Show debug information about rhythm detection progress."""
        if len(self.note_onsets) < 4:
            return  # Not enough data yet
            
        # Create a visual confidence meter
        meter_width = 20
        if self.confidence > 0:
            filled = int(self.confidence * meter_width)
            meter = f"{Fore.GREEN}{'█' * filled}{Fore.RED}{'░' * (meter_width - filled)}{Style.RESET_ALL}"
            
            # Output the current status
            print(f"\n{Fore.CYAN}Rhythm Analysis:{Style.RESET_ALL}")
            print(f"Notes collected: {len(self.note_onsets)}")
            print(f"Confidence: {self.confidence:.2f} {meter}")
            
            if self.bpm:
                print(f"Current BPM estimate: {self.bpm}")
                
            # Show potential BPM candidates
            if self.potential_bpms:
                candidates = ', '.join([f"{bpm} ({conf:.2f})" for bpm, conf in self.potential_bpms])
                print(f"Candidate BPMs: {candidates}")
                
            if self.confidence < self.min_confidence_threshold:
                print(f"{Fore.YELLOW}Keep playing to improve detection...{Style.RESET_ALL}")
            
    def stop(self):
        """Stop the beat tracker thread."""
        self.running = False
        print(f"{Fore.CYAN}Rhythm detector stopped.{Style.RESET_ALL}")
 
