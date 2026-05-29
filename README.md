# Aleatoric Music Generator

Veniamin Velikoretskikh - veniamin@pdx.edu - CS416P

## What I did

This program generates random music using chord progressions and sawtooth wave synthesis. Every time you run it, it picks a random song structure, key, tempo, and set of chord loops, then generates a melody on top. I also implemented the bass bonus which plays the chord root two octaves lower as a whole note under each measure.

## How it went

Getting the music theory math right was the trickiest part - figuring out how to convert roman numeral chord names into actual MIDI note numbers took some thinking. The sawtooth wave synthesis was pretty straightforward once I understood that audio is just arrays of numbers. The bass bonus ended up being simple since mixing two audio tracks is just adding two numpy arrays together.

## What is still to be done

- The melody sounds pretty random since notes are picked independently each time. A smarter generator would consider the previous note so there are smoother melodic lines.
- The sawtooth wave is pretty buzzy sounding. A proper ADSR envelope (attack, decay, sustain, release) would make it sound more like a real instrument.
- Notes are all the same volume. Varying the amplitude could add accents and make it feel more musical.

## How to run it in Linux, in an environment it might be different

Play directly through speakers:
```
python Aleotoric.py
```

Save to a WAV file:
```
python Aleotoric.py --output ALEATORIC.wav
```

With the bass bonus:
```
python Aleotoric.py --output ALEATORIC.wav --bass
```

## Requirements

```
numpy
scipy
sounddevice
```
