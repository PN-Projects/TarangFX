"""
Concurrency Manager - Prevents blocking with semaphores
Ensures no single user or operation blocks others
"""

import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, Set
from datetime import datetime, timedelta
from loguru import logger

from config import config


class ConcurrencyManager:
    """
    Manages concurrency limits to prevent blocking
    
    Key Features:
    - Global semaphores for downloads/uploads/processing
    - Per-user semaphores to prevent resource hogging
    - Automatic cleanup of expired files
    - No blocking operations
    """
    
    def __init__(self):
        # Global semaphores (limit total concurrent operations)
        self.download_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)
        self.upload_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_UPLOADS)
        self.processing_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_PROCESSING)
        
        # Per-user semaphores (prevent single user from hogging resources)
        self.user_semaphores: Dict[int, asyncio.Semaphore] = {}
        self.user_locks = asyncio.Lock()  # Lock for user_semaphores dict
        
        # Track active operations per user
        self.user_operations: Dict[int, Set[str]] = {}
        self.operations_lock = asyncio.Lock()
        
        # Track file creation times for cleanup
        self.file_timestamps: Dict[Path, datetime] = {}
        self.files_lock = asyncio.Lock()
        
        logger.info("✅ Concurrency manager initialized")
        logger.info(f"Global limits: {config.MAX_CONCURRENT_DOWNLOADS} downloads, "
                   f"{config.MAX_CONCURRENT_PROCESSING} processing")
        logger.info(f"Per-user limit: {config.MAX_OPERATIONS_PER_USER} concurrent operations")
    
    async def get_user_semaphore(self, user_id: int) -> asyncio.Semaphore:
        """
        Get or create semaphore for user - ASYNC
        Limits concurrent operations per user
        """
        async with self.user_locks:
            if user_id not in self.user_semaphores:
                self.user_semaphores[user_id] = asyncio.Semaphore(
                    config.MAX_OPERATIONS_PER_USER
                )
            return self.user_semaphores[user_id]
    
    async def can_user_process(self, user_id: int) -> bool:
        """
        Check if user can start new operation - ASYNC, NON-BLOCKING
        
        Returns:
            True if user has available slots
        """
        async with self.operations_lock:
            if user_id not in self.user_operations:
                return True
            return len(self.user_operations[user_id]) < config.MAX_OPERATIONS_PER_USER
    
    async def register_operation(self, user_id: int, operation_id: str):
        """Register a new operation for user - ASYNC"""
        async with self.operations_lock:
            if user_id not in self.user_operations:
                self.user_operations[user_id] = set()
            self.user_operations[user_id].add(operation_id)
            logger.debug(f"User {user_id} started operation {operation_id}")
    
    async def unregister_operation(self, user_id: int, operation_id: str):
        """Unregister completed operation - ASYNC"""
        async with self.operations_lock:
            if user_id in self.user_operations:
                self.user_operations[user_id].discard(operation_id)
                if not self.user_operations[user_id]:
                    del self.user_operations[user_id]
            logger.debug(f"User {user_id} completed operation {operation_id}")
    
    async def track_file(self, file_path: Path):
        """Track file creation time for cleanup - ASYNC"""
        async with self.files_lock:
            self.file_timestamps[file_path] = datetime.utcnow()
    
    async def cleanup_user_files(self, user_id: int):
        """
        Cleanup all files for a user - ASYNC, NON-BLOCKING
        Uses aiofiles for async file operations
        """
        user_dir = config.TEMP_DIR / str(user_id)
        
        if not user_dir.exists():
            return
        
        try:
            # Get all files in user directory
            files_to_delete = []
            for file_path in user_dir.iterdir():
                if file_path.is_file():
                    files_to_delete.append(file_path)
            
            # Delete files asynchronously
            for file_path in files_to_delete:
                try:
                    # Use executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, file_path.unlink)
                    
                    # Remove from tracking
                    async with self.files_lock:
                        self.file_timestamps.pop(file_path, None)
                        
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")
            
            # Try to remove directory
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, user_dir.rmdir)
            except OSError:
                pass  # Directory not empty, that's ok
            
            logger.info(f"Cleaned up {len(files_to_delete)} files for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up user {user_id} files: {e}")
    
    async def cleanup_expired(self):
        """
        Cleanup files older than session timeout - ASYNC
        Runs periodically in background
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=config.SESSION_TTL)
        
        expired_files = []
        
        async with self.files_lock:
            for file_path, timestamp in list(self.file_timestamps.items()):
                if timestamp < cutoff_time:
                    expired_files.append(file_path)
        
        if expired_files:
            logger.info(f"Cleaning up {len(expired_files)} expired files")
            
            for file_path in expired_files:
                try:
                    if file_path.exists():
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, file_path.unlink)
                    
                    async with self.files_lock:
                        self.file_timestamps.pop(file_path, None)
                        
                except Exception as e:
                    logger.warning(f"Could not delete expired file {file_path}: {e}")
    
    async def cleanup_all(self):
        """Cleanup all files on shutdown - ASYNC"""
        logger.info("Cleaning up all temporary files...")
        
        if not config.TEMP_DIR.exists():
            return
        
        try:
            count = 0
            for user_dir in config.TEMP_DIR.iterdir():
                if user_dir.is_dir():
                    for file_path in user_dir.iterdir():
                        try:
                            if file_path.is_file():
                                loop = asyncio.get_event_loop()
                                await loop.run_in_executor(None, file_path.unlink)
                                count += 1
                        except Exception as e:
                            logger.warning(f"Could not delete {file_path}: {e}")
                    
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, user_dir.rmdir)
                    except OSError:
                        pass
            
            logger.info(f"Cleaned up {count} files on shutdown")
            
        except Exception as e:
            logger.error(f"Error during cleanup_all: {e}")
    
    def get_stats(self) -> dict:
        """Get concurrency statistics"""
        return {
            "active_users": len(self.user_operations),
            "total_active_operations": sum(len(ops) for ops in self.user_operations.values()),
            "tracked_files": len(self.file_timestamps),
            "download_slots_available": self.download_semaphore._value,
            "upload_slots_available": self.upload_semaphore._value,
            "processing_slots_available": self.processing_semaphore._value,
        }


# Example usage in handlers:
"""
async def download_file(user_id, file):
    # Get user-specific semaphore (prevents one user from hogging resources)
    user_sem = await concurrency.get_user_semaphore(user_id)
    
    async with user_sem:  # Per-user limit
        async with concurrency.download_semaphore:  # Global limit
            # Download file
            file_path = await file.download()
            
            # Track for cleanup
            await concurrency.track_file(file_path)
            
            return file_path
"""
