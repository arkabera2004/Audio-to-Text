import os
import wave
import pyaudio
import speech_recognition as sr
from pathlib import Path
from datetime import datetime
import signal
import sys

class AudioTranscriber:
    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.recognizer = sr.Recognizer()
        self.is_recording = False

    def signal_handler(self, sig, frame):
        """Handle interrupt signal"""
        print("\nStopping recording...")
        self.is_recording = False

    def record_audio(self):
        """Record audio until Ctrl+C is pressed"""
        audio_config = {
            'chunk': 1024,
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 44100
        }

        try:
            p = pyaudio.PyAudio()
            frames = []

            # Setup signal handler
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # Start recording
            self.is_recording = True
            stream = p.open(
                format=audio_config['format'],
                channels=audio_config['channels'],
                rate=audio_config['rate'],
                input=True,
                frames_per_buffer=audio_config['chunk']
            )

            print("\nRecording... Press Ctrl+C to stop")

            while self.is_recording:
                data = stream.read(audio_config['chunk'], exception_on_overflow=False)
                frames.append(data)
                sys.stdout.write('.')
                sys.stdout.flush()

        except OSError as e:
            print(f"\nError accessing microphone: {e}")
            print("Please check microphone permissions in System Preferences > Security & Privacy > Microphone")
            return None
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return None
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            if 'p' in locals():
                p.terminate()

        # Save recording
        if frames:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"recording_{timestamp}.wav"
            
            with wave.open(str(filename), 'wb') as wf:
                wf.setnchannels(audio_config['channels'])
                wf.setsampwidth(p.get_sample_size(audio_config['format']))
                wf.setframerate(audio_config['rate'])
                wf.writeframes(b''.join(frames))
            return filename
        return None

    def transcribe_audio(self, audio_file):
        """Transcribe audio using speech recognition"""
        if not audio_file:
            return "No audio file to transcribe"
        try:
            with sr.AudioFile(str(audio_file)) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Speech recognition could not understand the audio"
        except sr.RequestError as e:
            return f"Could not request results; {str(e)}"

    def save_transcript(self, text):
        """Save transcript with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_text = f"Transcript - {timestamp}\n{'='*50}\n{text}\n"
        
        output_file = self.output_dir / "transcript.txt"
        with open(output_file, 'w') as f:
            f.write(formatted_text)
        return output_file

def main():
    transcriber = AudioTranscriber()
    
    try:
        print("Starting audio transcription...")
        print("Make sure microphone permissions are granted")
        
        # Record audio (now with Ctrl+C to stop)
        audio_file = transcriber.record_audio()
        if audio_file:
            print(f"\nAudio saved to: {audio_file}")
            
            # Transcribe audio
            print("\nTranscribing audio...")
            transcript = transcriber.transcribe_audio(audio_file)
            
            # Save transcript
            output_file = transcriber.save_transcript(transcript)
            print(f"\nTranscript saved to: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()