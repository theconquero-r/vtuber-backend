import os
import noisereduce as nr
import soundfile as sf
import librosa
import numpy as np

def clean_voice(input_path: str, output_path: str) -> str:
    """
    Cleans the audio by removing background noise and normalizing the volume.
    """
    try:
        # Load audio file
        data, rate = librosa.load(input_path, sr=None)
        
        # Perform noise reduction
        # We assume the first 0.5 seconds is background noise (silence from user)
        # If the audio is shorter than 0.5s, we use the whole audio for noise profiling
        noise_profile_len = min(int(rate * 0.5), len(data))
        if noise_profile_len == 0:
            return input_path # Too short to process
            
        noise_part = data[:noise_profile_len]
        
        # Apply noisereduce
        reduced_noise_data = nr.reduce_noise(y=data, sr=rate, y_noise=noise_part, prop_decrease=0.8)
        
        # Normalize volume
        max_val = np.max(np.abs(reduced_noise_data))
        if max_val > 0:
            normalized_data = reduced_noise_data / max_val
        else:
            normalized_data = reduced_noise_data
            
        # Save the cleaned audio
        sf.write(output_path, normalized_data, rate)
        
        return output_path
    except Exception as e:
        print(f"Error in audio cleaning: {e}")
        # In case of error, return the original file
        return input_path
