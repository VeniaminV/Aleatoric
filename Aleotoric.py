# CS416 - Aleatoric Music Assignment
# Veniamin Velikoretskikh veniamin@pdx.edu

#Made in VS code, this is what i needed to run to output to a wav file:

# & C:/Users/venia/.virtualenvs/CS302-P89zmmFC/Scripts/python.exe 
# "c:/Users/venia/OneDrive/Desktop/CS416P Computer music and sound/Aleatoric/Aleotoric.py" --output ALEATORIC.wav

# This program generates random music using chord progressions and sawtooth waves.
# You run it with --output somefile.wav to save it, or without to play it on speakers.
# I also did the --bass bonus which adds a low bass note under each chord.

import argparse
import random
import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd
import time

SAMPLE_RATE = 48000

# These numbers are how many semitones each note is above the root/starting note.
# So if root is C, the scale is: C, D, E, F, G, A, B (then C again an octave up)
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

# I = first note of scale, ii = second note, etc.
DEGREE = {'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'iv': 3, 'V': 4, 'vi': 5, 'vii': 6}

# A chord is built by stacking notes on top of each other.
# These numbers are semitone offsets FROM the chord's root note.
# Major chords: root + 4 semitones + 7 semitones (sounds happy)
# Minor chords: root + 3 semitones + 7 semitones (sounds sad)
# The 'iv' is a "borrowed" minor chord - it normally would be major in a major key
# but composers borrow it from the minor version for a darker sound.
CHORD_INTERVALS = {
    'I':   [0, 4, 7],  # major
    'ii':  [0, 3, 7],  # minor
    'iii': [0, 3, 7],  # minor
    'IV':  [0, 4, 7],  # major
    'V':   [0, 4, 7],  # major
    'vi':  [0, 3, 7],  # minor
    'iv':  [0, 3, 7],  # minor (borrowed from parallel minor key)
    'vii': [0, 3, 6],  # diminished (rare but included for completeness)
}


SONG_STRUCTURES = ["AABB/CC", "ABAB/CD", "AB/CDDD"]

# These are the 10 chord loops from the assignment.
CHORD_LOOPS = [
    ['I', 'IV', 'ii', 'V'],
    ['I', 'vi', 'ii', 'V'],
    ['I', 'iii', 'IV', 'iv'],
    ['I', 'V', 'ii', 'V'],
    ['I', 'vi', 'IV', 'V'],
    ['IV', 'I', 'vi', 'IV'],
    ['I', 'V', 'vi', 'I'],
    ['I', 'IV', 'iv', 'I'],
    ['IV', 'V', 'I', 'I'],
    ['vi', 'IV', 'I', 'V'],
]

# MIDI note numbers for A3 and A4.
A3_MIDI = 57
A4_MIDI = 69


# MIDI note number to frequency in Hz 
# A4 (MIDI 69) = 440 Hz. Every 12 semitones = double the frequency (one octave up).
# So MIDI 70 = 440 * 2^(1/12), MIDI 81 = 440 * 2^(12/12) = 880 Hz, etc.
def midi_to_freq(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


#get all notes in the major scale starting at root_midi
def get_scale_notes(root_midi):
    return [root_midi + interval for interval in MAJOR_SCALE_INTERVALS]


# get the chord tones (as MIDI notes) for a given chord numeral
def get_chord_notes(root_midi, numeral):
    # First find which scale degree this chord is built on
    degree_idx = DEGREE[numeral]
    # Then find the actual MIDI note for that scale degree
    chord_root = root_midi + MAJOR_SCALE_INTERVALS[degree_idx]
    # Then build the chord by adding the chord intervals on top
    return [chord_root + offset for offset in CHORD_INTERVALS[numeral]]


#Sawtooth wave generator
def make_sawtooth(freq, duration, amplitude=0.3):
    # Figure out how many samples we need
    n_samples = int(SAMPLE_RATE * duration)

    # t is an array of time values: [0, 1/48000, 2/48000, ..., (n-1)/48000]
    # np.arange gives us [0, 1, 2, ..., n-1] and dividing by SAMPLE_RATE converts to seconds
    t = np.arange(n_samples) / SAMPLE_RATE

    # This is the sawtooth formula. t * freq tells us how many complete cycles have passed.
    # Subtracting floor(t*freq + 0.5) removes the integer part, leaving just the fractional ramp.
    # Multiplying by 2 scales it from [-1, 1].
    wave = 2.0 * (t * freq - np.floor(t * freq + 0.5))

    # The envelope makes the note fade out. ** 0.3 gives a curve that fades quickly at first
    # then more slowly - sounds more natural than a straight linear fade.
    # linspace(1.0, 0.0, n) gives [1.0, ..., 0.0] - starts full volume, ends at silence.
    envelope = np.linspace(1.0, 0.0, n_samples) ** 0.3

    # Multiply wave * envelope * amplitude and convert to float32, required for audio
    return (wave * envelope * amplitude).astype(np.float32)


#Main song generation function
def generate_song(bass=False):

    # Pick random song parameters
    structure_str = random.choice(SONG_STRUCTURES)
    root_midi = random.randint(A3_MIDI, A4_MIDI)
    tempo = random.randint(80, 160)  # beats per minute


    beat_duration = 60.0 / tempo
    measure_duration = beat_duration * 4
    eighth_duration = beat_duration / 2

    print(f"Structure: {structure_str}")
    print(f"Key root: MIDI {root_midi} ({midi_to_freq(root_midi):.1f} Hz)")
    print(f"Tempo: {tempo} BPM")

    # Parse the structure string into a list of letters, ignoring the '/'
    # "AABB/CC" becomes ['A', 'A', 'B', 'B', 'C', 'C']
    labels_in_order = [c for c in structure_str if c.isalpha()]

    # Get just the unique labels to know how many chord loops we need
    unique_labels = list(dict.fromkeys(labels_in_order))

    # Pick a random chord loop for each unique label, no repeats allowed.
    chosen_loops = random.sample(CHORD_LOOPS, len(unique_labels))
    label_to_loop = dict(zip(unique_labels, chosen_loops))

    print("Chord loops:")
    for label, loop in label_to_loop.items():
        print(f"  {label}: {' - '.join(loop)}")

    # Get the notes in our key's major scale
    scale = get_scale_notes(root_midi)

    # Build the audio section by section
    song_chunks = []

    for label in labels_in_order:
        loop = label_to_loop[label]

        for numeral in loop:
            # Get the MIDI notes that make up this chord
            raw_chord_notes = get_chord_notes(root_midi, numeral)

            # Clamp notes to the first octave above the root.
            # "% 12" gets the note's position within an octave (0-11),
            # then adding root_midi puts it in the right octave range.
            chord_tones = [n % 12 + root_midi for n in raw_chord_notes]

            # Generate the melody: 8 eighth notes per measure
            melody_notes = []
            for _ in range(8):
                # 80% chance of picking a chord tone, 20% any scale note
                if random.random() < 0.8:
                    note = random.choice(chord_tones)
                else:
                    note = random.choice(scale)
                freq = midi_to_freq(note)
                melody_notes.append(make_sawtooth(freq, eighth_duration, amplitude=0.35))

            
            melody_wave = np.concatenate(melody_notes)

            if bass:
                # Bass bonus: play the chord root two octaves lower as a whole note
                # Two octaves = 24 semitones lower in MIDI
                bass_midi = chord_tones[0] - 24
                bass_freq = midi_to_freq(bass_midi)
                bass_wave = make_sawtooth(bass_freq, measure_duration, amplitude=0.25)

                # Mix the two tracks together by adding their arrays.
                max_len = max(len(melody_wave), len(bass_wave))
                mixed = np.zeros(max_len, dtype=np.float32)
                mixed[:len(melody_wave)] += melody_wave
                mixed[:len(bass_wave)] += bass_wave

                song_chunks.append(mixed)
            else:
                song_chunks.append(melody_wave)

    # Put all the chunks together into one big array
    full_audio = np.concatenate(song_chunks)

    # Normalize: make sure the loudest point is at 90% volume so we don't clip.
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = full_audio / peak * 0.9

    return full_audio



def main():
    parser = argparse.ArgumentParser(description="Generate random aleatoric music")
    parser.add_argument("--output", metavar="FILENAME.wav",
                        help="Save to a WAV file instead of playing through speakers")
    parser.add_argument("--bass", action="store_true",
                        help="Add bass track (bonus): plays chord root two octaves lower")
    parser.add_argument("--seed", type=int, default=None,
                        help="Set random seed for reproducible output (useful for testing)")
    args = parser.parse_args()

    # Setting a seed makes random() give the same sequence every time.
    # Good for debugging - you get the same song each run.
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    print("Generating song...")
    audio = generate_song(bass=args.bass)
    print(f"Total length: {len(audio) / SAMPLE_RATE:.1f} seconds")

    if args.output:
        # WAV files store audio as integers, not floats.
        # Our audio is in range [-1.0, 1.0]. int16 range is [-32768, 32767].
        # Multiply by 32767 to scale up, then cast to int16.
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(args.output, SAMPLE_RATE, audio_int16)
        print(f"Saved to {args.output}")
    else:
        try:
            print("Playing audio... (Ctrl+C to stop)")
            sd.play(audio, SAMPLE_RATE)
            while sd.get_stream().active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            sd.stop()
            print("\nStopped.")
        except ImportError:
            print("sounddevice not installed. Use --output to save as WAV instead.")
        except Exception as e:
            print(f"Playback failed: {e}")
            print("Try using --output to save as WAV instead.")

if __name__ == "__main__":
    main()