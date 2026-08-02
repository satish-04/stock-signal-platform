"""
Signal processing worker.
"""

import asyncio
from datetime import datetime

from app.core.config import get_settings, Settings


class SignalWorker:
    """
    Background worker for processing trading signals.
    
    Listens to signal queues and processes them
    through the full trade workflow.
    """
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.running = False
    
    async def start(self) -> None:
        """Start the signal worker."""
        self.running = True
        print(f"[{datetime.utcnow()}] SignalWorker started")
        
        while self.running:
            try:
                # Check for new signals
                await self._process_pending_signals()
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"[{datetime.utcnow()}] Error processing signals: {e}")
                await asyncio.sleep(10)  # Longer wait on error
    
    async def _process_pending_signals(self) -> None:
        """Process pending signals."""
        # Placeholder - would check Redis queue
        print(f"[{datetime.utcnow()}] Checking for pending signals...")
    
    async def stop(self) -> None:
        """Stop the signal worker."""
        self.running = False
        print(f"[{datetime.utcnow()}] SignalWorker stopped")


async def main():
    """Main entry point for the worker."""
    import signal
    import sys
    
    worker = SignalWorker()
    
    # Handle SIGINT gracefully
    def signal_handler(sig, frame):
        print("\nShutting down worker...")
        asyncio.create_task(worker.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
