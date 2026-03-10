
import unittest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from handlers.audio import handle_audio_file
from config import config

class TestPremiumLogic(unittest.TestCase):
    def setUp(self):
        self.concurrency = AsyncMock()
        self.concurrency.can_user_process.return_value = True
        self.concurrency.get_user_semaphore.return_value = AsyncMock()
        self.concurrency.download_semaphore = AsyncMock()
        
        self.event = AsyncMock()
        self.event.sender_id = 12345
        self.event.message.audio.size = 1024 * 1024 # 1MB
        self.event.message.audio.attributes = [MagicMock(file_name="test.flac")]
        
        self.bot = AsyncMock()

    async def test_free_user_lossless_restriction(self):
        """Test that free users cannot process FLAC"""
        # Mock DB to return free user
        with unittest.mock.patch('core.database.db.is_premium', new_callable=AsyncMock) as mock_is_premium:
            mock_is_premium.return_value = False
            
            # Mock concurrency to avoid actual download
            with unittest.mock.patch('handlers.audio.download_file_async', new_callable=AsyncMock) as mock_download:
                mock_download.return_value = "dummy/path/test.flac"
                
                # Mock format detection
                with unittest.mock.patch('handlers.audio.detect_format_async', new_callable=AsyncMock) as mock_detect:
                    mock_detect.return_value = {'format': 'FLAC', 'duration': 60}
                    
                    # Run handler
                    await handle_audio_file(self.event, self.bot, self.concurrency)
                    
                    # Verify "Restricted" message
                    # We expect status_msg.edit to be called with restriction text
                    # status_msg is start_msg which is result of event.respond
                    # So we check the mock returned by event.respond
                    status_msg = self.event.respond.return_value
                    args, _ = status_msg.edit.call_args
                    self.assertIn("Premium Feature", args[0])
                    self.assertIn("Lossless Audio", args[0])

    async def test_premium_user_lossless_allowed(self):
        """Test that premium users CAN process FLAC"""
        # Mock DB to return premium user
        with unittest.mock.patch('core.database.db.is_premium', new_callable=AsyncMock) as mock_is_premium:
            mock_is_premium.return_value = True
            
            with unittest.mock.patch('handlers.audio.download_file_async', new_callable=AsyncMock) as mock_download:
                mock_download.return_value = "dummy/path/test.flac"
                
                with unittest.mock.patch('handlers.audio.detect_format_async', new_callable=AsyncMock) as mock_detect:
                    mock_detect.return_value = {'format': 'FLAC', 'duration': 60}
                    
                    # Mock UI import to avoid errors
                    with unittest.mock.patch('handlers.ui.get_processing_menu') as mock_menu:
                        
                         await handle_audio_file(self.event, self.bot, self.concurrency)
                         
                         # Verify "Ready" message
                         status_msg = self.event.respond.return_value
                         args, _ = status_msg.edit.call_args
                         self.assertIn("Audio File Ready", args[0])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unittest.main())
