
import asyncio
import numpy as np
import soundfile as sf
from pathlib import Path
from processors import AsyncAudioProcessor
from models import ProcessingOperation

async def test_effects():
    # Create dummy audio
    sr = 44100
    t = np.linspace(0, 5, sr*5)
    y = 0.5 * np.sin(2 * np.pi * 440 * t) # 440Hz sine wave
    
    input_file = Path("test_input.wav")
    sf.write(str(input_file), y, sr)
    
    # Test Bass Boost
    print("Testing Bass Boost...")
    op_bass = ProcessingOperation(
        operation_type="effect",
        parameters={"effect_type": "bass_boost", "frequency": 60, "gain_db": 6}
    )
    
    processor = AsyncAudioProcessor(12345, input_file, [op_bass])
    out_bass = await processor.process()
    print(f"Bass Boost output: {out_bass}")
    assert out_bass.exists()
    
    # Test Vocal Enhance
    print("\nTesting Vocal Enhance...")
    op_vocal = ProcessingOperation(
        operation_type="effect",
        parameters={"effect_type": "vocal_enhance", "vocal_type": "male"}
    )
    
    processor = AsyncAudioProcessor(12345, input_file, [op_vocal])
    out_vocal = await processor.process()
    print(f"Vocal Enhance output: {out_vocal}")
    assert out_vocal.exists()
    
    # Cleanup
    input_file.unlink()
    out_bass.unlink()
    out_vocal.unlink()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_effects())
