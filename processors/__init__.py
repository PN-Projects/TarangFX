"""
Async Audio Processing Pipeline
All CPU-intensive work runs in executor to not block event loop
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import soundfile as sf
import librosa
import numpy as np
from pedalboard import Pedalboard, Reverb, Delay, Distortion, Chorus, Phaser, Gain, HighpassFilter, LowShelfFilter, PeakFilter, Compressor

from models import ProcessingOperation
from config import config


class AsyncAudioProcessor:
    """Async Audio Processor using Pedalboard and FFmpeg"""
    
    def __init__(self, user_id: int, input_file: Path, operations: List[ProcessingOperation]):
        self.user_id = user_id
        self.temp_dir = config.TEMP_DIR / str(user_id)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.input_file = input_file
        self.operations = sorted(operations, key=lambda x: x.priority)
        self.current_file = input_file
        self.temp_files = []
    
    async def process(self) -> Path:
        """
        Process audio through operation pipeline - ASYNC
        
        Returns:
            Path to final processed file
        """
        try:
            logger.info(f"[Processor] Starting pipeline for user {self.user_id}: {len(self.operations)} operations")
            
            for i, operation in enumerate(self.operations):
                logger.info(f"[Processor] Operation {i+1}/{len(self.operations)}: {operation.operation_type}")
                
                # Execute operation (CPU-bound work in executor)
                self.current_file = await self._execute_operation(operation)
                self.temp_files.append(self.current_file)
            
            # Generate final meaningful filename
            final_name_parts = [self.input_file.stem]
            ext = self.current_file.suffix
            
            for op in self.operations:
                top = op.operation_type
                params = op.parameters
                
                if top == "effect":
                    fx = params.get('effect_type', 'fx')
                    if fx == "bass_boost": final_name_parts.append("bass")
                    elif fx == "vocal_enhance": final_name_parts.append("vocal")
                    else: final_name_parts.append(fx)
                elif top == "normalize":
                    final_name_parts.append("norm")
                elif top == "resample":
                    final_name_parts.append(f"{params['sample_rate']}hz")
                elif top == "bitrate":
                    final_name_parts.append(f"{params['bitrate']}k")
                # Skip convert suffix as extension changes
            
            # Construct new filename
            final_filename = "_".join(final_name_parts) + ext
            final_path = self.current_file.parent / final_filename
            
            # Rename if different
            if final_path != self.current_file:
                # If target exists, overwrite (shutil.move or replace)
                import shutil
                shutil.move(str(self.current_file), str(final_path))
                self.current_file = final_path
            
            logger.info(f"[Processor] Pipeline complete: {self.current_file}")
            return self.current_file

        except Exception as e:
            logger.error(f"[Processor] Error in pipeline: {e}")
            raise

    def _flac_compression_level(self, bitrate: int) -> int:
        """Map a bitrate-style selection onto FFmpeg FLAC compression levels."""
        if bitrate >= 30000:
            return 0
        if bitrate >= 20000:
            return 2
        if bitrate >= 12000:
            return 4
        if bitrate >= 8000:
            return 6
        if bitrate >= 4000:
            return 8
        return 12
    
    async def _execute_operation(self, operation: ProcessingOperation) -> Path:
        """Execute single operation - ASYNC"""
        op_type = operation.operation_type
        params = operation.parameters
        
        if op_type == "convert":
            return await self._convert_format(params)
        elif op_type == "resample":
            return await self._resample(params)
        elif op_type == "bitrate":
            return await self._adjust_bitrate(params)
        elif op_type == "effect":
            return await self._apply_effect(params)
        elif op_type == "normalize":
            return await self._normalize(params)
        elif op_type == "trim":
            return await self._trim(params)
        else:
            logger.warning(f"Unknown operation: {op_type}")
            return self.current_file
    
    async def _convert_format(self, params: Dict) -> Path:
        """Convert format using FFmpeg - ASYNC (runs in executor)"""
        output_ext = params.get('extension', '.mp3')
        
        # Smart codec selection
        codec_map = {
            '.mp3': 'libmp3lame',
            '.aac': 'aac',
            '.m4a': 'aac',
            '.ogg': 'libopus',
            '.opus': 'libopus',
            '.flac': 'flac',
            '.wav': 'pcm_s16le',
            '.aiff': 'pcm_s16be',
            '.alac': 'alac',
        }
        
        default_codec = codec_map.get(output_ext, 'libmp3lame')
        start_codec = params.get('codec', default_codec)

        # FFmpeg cannot write to a .alac container, it must be .m4a
        if output_ext == '.alac':
            output_ext = '.m4a'
            start_codec = 'alac'
            
        output_path = self.current_file.parent / f"convert_{self.current_file.stem}{output_ext}"
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg', '-i', str(self.current_file),
            '-y',  # Overwrite
            '-acodec', start_codec,
        ]
        
        # Handle bitrate (only for lossy formats)
        bitrate = params.get('bitrate')
        if bitrate:
            if output_ext in ['.mp3', '.aac', '.m4a', '.ogg', '.opus']:
                cmd.extend(['-b:a', f"{bitrate}k"])
            elif output_ext == '.flac':
                cmd.extend(['-compression_level', str(self._flac_compression_level(int(bitrate)))])
             
        # Map metadata if needed (FFmpeg does this by default usually)
        
        cmd.append(str(output_path))
        
        # Run in executor (blocking subprocess)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_ffmpeg, cmd)
        
        return output_path
    
    async def _resample(self, params: Dict) -> Path:
        """Resample audio - ASYNC (using FFmpeg)"""
        target_sr = params['sample_rate']
        output_path = self.current_file.parent / f"resample_{target_sr}_{self.current_file.stem}.wav"
        
        # Use FFmpeg for high-quality resampling (soxr)
        cmd = [
            'ffmpeg', '-i', str(self.current_file),
            '-y',
            '-ar', str(target_sr),
            str(output_path)
        ]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_ffmpeg, cmd)
        
        return output_path

    async def _adjust_bitrate(self, params: Dict) -> Path:
        """Adjust bitrate - ASYNC"""
        bitrate = params['bitrate']
        
        # If original, return current file without changes
        if bitrate == 'original':
            return self.current_file

        # When a convert step is already present, bitrate should be carried by
        # that final conversion so we do not transcode twice.
        if any(op.operation_type == 'convert' for op in self.operations):
            return self.current_file

        source_ext = self.current_file.suffix.lower()
        if source_ext == '.alac':
            source_ext = '.m4a'

        codec_map = {
            '.mp3': 'libmp3lame',
            '.aac': 'aac',
            '.m4a': 'aac',
            '.ogg': 'libopus',
            '.opus': 'libopus',
            '.flac': 'flac',
            '.wav': 'pcm_s16le',
            '.aiff': 'pcm_s16be',
        }
        target_codec = codec_map.get(source_ext, 'libmp3lame')

        output_path = self.current_file.parent / f"bitrate_{bitrate}k_{self.current_file.stem}{source_ext}"

        cmd = [
            'ffmpeg', '-i', str(self.current_file),
            '-y',
            '-acodec', target_codec,
        ]

        if source_ext == '.flac':
            cmd.extend(['-compression_level', str(self._flac_compression_level(int(bitrate)))])
        elif source_ext in ['.mp3', '.aac', '.m4a', '.ogg', '.opus']:
            cmd.extend(['-b:a', f"{bitrate}k"])
        else:
            return self.current_file

        cmd.append(str(output_path))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_ffmpeg, cmd)
        
        return output_path
    
    async def _apply_effect(self, params: Dict) -> Path:
        """Apply effect using pedalboard - ASYNC"""
        # Ensure input is WAV for soundfile/pedalboard compatibility
        temp_wav = self.current_file
        
        if self.current_file.suffix.lower() not in ['.wav', '.aiff', '.flac']:
             temp_wav = self.current_file.parent / f"temp_effect_input_{self.current_file.stem}.wav"
             # Use safe conversion
             cmd = ['ffmpeg', '-i', str(self.current_file), '-y', str(temp_wav)]
             loop = asyncio.get_event_loop()
             await loop.run_in_executor(None, self._run_ffmpeg, cmd)
             self.temp_files.append(temp_wav)

        effect_type = params['effect_type']
        output_path = self.current_file.parent / f"effect_{effect_type}.wav"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._apply_effect_sync,
            temp_wav, # Use the safe WAV
            output_path,
            params
        )
        
        return output_path

    async def _normalize(self, params: Dict) -> Path:
        """Normalize audio - ASYNC (using FFmpeg loudnorm)"""
        output_path = self.current_file.parent / f"normalized_{self.current_file.stem}.wav"
        
        # Use EBU R128 loudness normalization
        cmd = [
            'ffmpeg', '-i', str(self.current_file),
            '-y',
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
            str(output_path)
        ]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_ffmpeg, cmd)
        
        return output_path
    
    async def _trim(self, params: Dict) -> Path:
        """Trim audio - ASYNC"""
        start = params.get('start', 0)
        end = params.get('end', None)
        output_path = self.current_file.parent / f"trimmed_{self.current_file.stem}.wav"
        
        cmd = ['ffmpeg', '-i', str(self.current_file), '-y']
        
        if end:
            cmd.extend(['-ss', str(start), '-t', str(end - start)])
        else:
            cmd.extend(['-ss', str(start)])
        
        cmd.append(str(output_path))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_ffmpeg, cmd)
        
        return output_path
    
    # ========================================================================
    # SYNCHRONOUS HELPERS (Run in executor)
    # ========================================================================
    
    def _run_ffmpeg(self, cmd: List[str]):
        """Run FFmpeg command - BLOCKING (called in executor)"""
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")
    
    
    def _apply_effect_sync(self, input_path: Path, output_path: Path, params: Dict):
        """Apply effect - BLOCKING"""
        y, sr = sf.read(str(input_path))
        
        effect_type = params['effect_type']
        intensity = params.get('intensity', 0.5)
        
        effects_list = []
        
        # Create effect
        if effect_type == "reverb":
            effects_list.append(Reverb(room_size=intensity, wet_level=intensity * 0.5))
        elif effect_type == "delay":
            effects_list.append(Delay(delay_seconds=0.2 * intensity, mix=intensity * 0.4))
        elif effect_type == "distortion":
            effects_list.append(Distortion(drive_db=intensity * 30))
        elif effect_type == "chorus":
            effects_list.append(Chorus(rate_hz=1.0 + intensity, mix=intensity * 0.7))
        elif effect_type == "flanger":
            effects_list.append(Chorus(rate_hz=0.5 + intensity, mix=intensity * 0.6))
        elif effect_type == "phaser":
            effects_list.append(Phaser(rate_hz=1.0 + intensity, mix=intensity * 0.5))
        elif effect_type == "bass_boost":
            freq = params.get('frequency', 60)
            gain = params.get('gain_db', 3)
            effects_list.append(PeakFilter(cutoff_frequency_hz=freq, gain_db=gain, q=1.0))
        elif effect_type == "vocal_enhance":
            v_type = params.get('vocal_type', 'male')
            if v_type == 'male':
                effects_list.append(HighpassFilter(cutoff_frequency_hz=80))
                effects_list.append(PeakFilter(cutoff_frequency_hz=150, gain_db=2.0, q=1.0))
                effects_list.append(PeakFilter(cutoff_frequency_hz=4000, gain_db=2.0, q=1.0))
            else:
                effects_list.append(HighpassFilter(cutoff_frequency_hz=150))
                effects_list.append(PeakFilter(cutoff_frequency_hz=250, gain_db=2.0, q=1.0))
                effects_list.append(PeakFilter(cutoff_frequency_hz=4000, gain_db=2.0, q=1.0))
            
            effects_list.append(Compressor(threshold_db=-15, ratio=3))
        else:
            effects_list.append(Gain(gain_db=0))
        
        # Apply
        board = Pedalboard(effects_list)
        y_effected = board(y, sr)
        
        sf.write(str(output_path), y_effected, sr)
    
    
    async def cleanup(self):
        """Cleanup temporary files - ASYNC"""
        for temp_file in self.temp_files:
            if temp_file != self.current_file and temp_file.exists():
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, temp_file.unlink)
                except Exception as e:
                    logger.warning(f"Could not delete temp file {temp_file}: {e}")
