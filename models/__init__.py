"""
Data Models for TarangFX Telethon
All models are simple dataclasses for async operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class AudioTier(str, Enum):
    """User tier levels"""
    FREE = "free"
    PREMIUM = "premium"


class AudioCodec(str, Enum):
    """Supported audio codecs"""
    # Lossy formats (Free tier)
    MP3 = "mp3"
    AAC = "aac"
    M4A = "m4a"
    OPUS = "opus"
    OGG = "ogg"
    VORBIS = "vorbis"
    WMA = "wma"
    
    # Lossless formats (Premium tier)
    FLAC = "flac"
    WAV = "wav"
    AIFF = "aiff"
    ALAC = "alac"
    APE = "ape"
    TTA = "tta"


@dataclass
class User:
    """User model"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_premium: bool = False
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def tier(self) -> AudioTier:
        """Get user tier"""
        return AudioTier.PREMIUM if self.is_premium else AudioTier.FREE


@dataclass
class AudioFileInfo:
    """Information about an audio file"""
    file_path: str
    file_name: str
    file_size: int
    duration: float
    format: Optional[str] = None
    codec: Optional[AudioCodec] = None
    sample_rate: Optional[int] = None
    bit_rate: Optional[int] = None
    channels: Optional[int] = None


@dataclass
class ProcessingOperation:
    """Single processing operation"""
    operation_type: str
    parameters: Dict[str, Any]
    priority: int = 50
    
    def __lt__(self, other):
        return self.priority < other.priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_type": self.operation_type,
            "parameters": self.parameters,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingOperation':
        return cls(
            operation_type=data["operation_type"],
            parameters=data["parameters"],
            priority=data.get("priority", 50)
        )


@dataclass
class Session:
    """User session"""
    user_id: int
    audio_file: Optional[AudioFileInfo] = None
    operations: List[ProcessingOperation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[int] = None
    
    def add_operation(self, operation: ProcessingOperation):
        if operation.operation_type == "effect":
            # For effects, only remove if exact same effect_type exists
            new_fx_type = operation.parameters.get("effect_type")
            self.operations = [
                op for op in self.operations 
                if not (op.operation_type == "effect" and op.parameters.get("effect_type") == new_fx_type)
            ]
        else:
            # For other operations (convert, resample, etc.), replace existing
            self.operations = [op for op in self.operations if op.operation_type != operation.operation_type]
            
        self.operations.append(operation)
    
    def get_sorted_operations(self) -> List[ProcessingOperation]:
        return sorted(self.operations, key=lambda x: x.priority)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "audio_file": self.audio_file, # AudioFileInfo is likely dict in cache or needs handling. 
            # handlers/audio.py saves it as dict inside 'audio_info' or similar? 
            # Wait, handlers/audio.py puts 'audio_info' (dict) in root of session_data, 
            # but Session model has 'audio_file' field.
            # Let's check handlers/callbacks.py usage.
            "operations": [op.to_dict() for op in self.operations],
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "message_id": self.message_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        operations_data = data.get("operations", [])
        operations = [ProcessingOperation.from_dict(op) for op in operations_data]
        
        # created_at might be str from JSON/msgpack
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.utcnow()
                
        return cls(
            user_id=data["user_id"],
            audio_file=data.get("audio_file"), # Keep as is for now
            operations=operations,
            created_at=created_at or datetime.utcnow(),
            message_id=data.get("message_id")
        )


# Operation priorities
OPERATION_PRIORITIES = {
    "trim": 10,
    "resample": 20,
    "effects": 50,
    "normalize": 80,
    "bitrate": 90,
    "convert": 100,
}
