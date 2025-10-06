"""
Batch Processing Utilities for SDK Agent Tools.

Provides efficient batch processing for analyzing multiple files,
reducing overhead and improving performance for large-scale analysis.
"""

import asyncio
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
import logging

from sdk_agent.error_formatter import ErrorFormatter, log_structured_error

logger = logging.getLogger("sdk_agent.tools.batch")


async def process_files_in_batches(
    files: List[Path],
    process_func: Callable,
    batch_size: int = 10,
    max_concurrency: int = 5,
    progress_callback: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple files in batches with controlled concurrency.

    Args:
        files: List of file paths to process
        process_func: Async function to process each file
        batch_size: Number of files per batch (must be >= 1)
        max_concurrency: Maximum concurrent operations (must be >= 1)
        progress_callback: Optional callback for progress updates

    Returns:
        List of processing results

    Raises:
        ValueError: If batch_size or max_concurrency is less than 1

    Performance:
        - Processes files in batches to reduce overhead
        - Controls concurrency to avoid resource exhaustion
        - Provides progress feedback for long-running operations
    """
    # Validate configuration parameters
    if batch_size < 1:
        raise ValueError(
            f"batch_size must be >= 1, got {batch_size}. "
            "Use larger batch sizes for better performance."
        )
    if max_concurrency < 1:
        raise ValueError(
            f"max_concurrency must be >= 1, got {max_concurrency}. "
            "Recommended range: 3-10 for optimal performance."
        )
    if max_concurrency > 50:
        logger.warning(
            f"max_concurrency={max_concurrency} is very high. "
            "Consider using 3-10 to avoid resource exhaustion."
        )

    results = []
    total_files = len(files)

    logger.info(
        f"Starting batch processing: {total_files} files, "
        f"batch_size={batch_size}, max_concurrency={max_concurrency}"
    )

    # Process in batches
    for batch_idx in range(0, total_files, batch_size):
        batch = files[batch_idx:batch_idx + batch_size]
        batch_num = (batch_idx // batch_size) + 1
        total_batches = (total_files + batch_size - 1) // batch_size

        logger.debug(f"Processing batch {batch_num}/{total_batches}: {len(batch)} files")

        # Process batch with controlled concurrency
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_with_semaphore(file_path: Path) -> Dict[str, Any]:
            """Process single file with semaphore control."""
            async with semaphore:
                try:
                    result = await process_func(file_path)
                    return {
                        "file": str(file_path),
                        "success": True,
                        "result": result
                    }
                except Exception as e:
                    # Use standardized error formatting
                    log_structured_error(
                        logger,
                        e,
                        component="batch_processor",
                        context={
                            "file_path": str(file_path),
                            "batch_num": batch_num,
                            "total_batches": total_batches
                        }
                    )
                    return {
                        "file": str(file_path),
                        "success": False,
                        "error": ErrorFormatter.format_processing_error(
                            item=str(file_path),
                            error=e,
                            batch_info={
                                "batch": batch_num,
                                "total_batches": total_batches
                            }
                        )
                    }

        # Process batch concurrently
        batch_results = await asyncio.gather(
            *[process_with_semaphore(f) for f in batch],
            return_exceptions=True
        )

        # Handle any exceptions from gather
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing exception: {result}")
                results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                results.append(result)

        # Progress callback
        if progress_callback:
            progress = {
                "batch": batch_num,
                "total_batches": total_batches,
                "processed": min(batch_idx + batch_size, total_files),
                "total": total_files,
                "success_count": sum(1 for r in results if r.get("success", False)),
                "error_count": sum(1 for r in results if not r.get("success", True))
            }
            progress_callback(progress)

    logger.info(
        f"Batch processing complete: {len(results)} files, "
        f"{sum(1 for r in results if r.get('success', False))} successful"
    )

    return results


async def analyze_directory_optimized(
    directory: Path,
    pattern: str,
    recursive: bool,
    file_type_detector: Callable,
    agent_getter: Callable,
    batch_size: int = 10,
    max_concurrency: int = 5
) -> Dict[str, Any]:
    """
    Optimized directory analysis with batch processing.

    Args:
        directory: Directory to analyze
        pattern: File pattern (glob)
        recursive: Search recursively
        file_type_detector: Function to detect file type
        agent_getter: Function to get agent for file type
        batch_size: Files per batch
        max_concurrency: Max concurrent operations

    Returns:
        Analysis results with statistics
    """
    logger.info(f"Analyzing directory: {directory}, pattern: {pattern}")

    # Find files
    if recursive:
        files = list(directory.glob(pattern))
    else:
        # Non-recursive: strip leading **/ from pattern
        non_recursive_pattern = pattern.lstrip("**/")
        if not non_recursive_pattern or non_recursive_pattern == pattern:
            non_recursive_pattern = pattern
        files = list(directory.glob(non_recursive_pattern))

    if not files:
        return {
            "content": [{
                "type": "text",
                "text": f"No files found matching pattern: {pattern}"
            }],
            "total_files": 0,
            "results": []
        }

    logger.info(f"Found {len(files)} files to analyze")

    # Group files by type for optimized processing
    files_by_type = {}
    for file_path in files:
        file_type = file_type_detector(str(file_path))
        if file_type:
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_path)

    # Process each file type in batches
    all_results = []
    progress_data = {
        "current": 0,
        "total": len(files)
    }

    def show_progress(progress: Dict[str, Any]):
        """Display progress to user."""
        progress_data["current"] = progress["processed"]
        percentage = (progress["processed"] / progress["total"]) * 100
        logger.info(
            f"Progress: {progress['processed']}/{progress['total']} "
            f"({percentage:.1f}%) - "
            f"Success: {progress['success_count']}, "
            f"Errors: {progress['error_count']}"
        )

    for file_type, type_files in files_by_type.items():
        logger.info(f"Processing {len(type_files)} {file_type} files")

        # Get agent for this file type
        try:
            agent = agent_getter(file_type)
        except Exception as e:
            logger.error(f"Failed to get agent for {file_type}: {e}")
            continue

        # Process function for this file type
        async def process_file(file_path: Path) -> Dict[str, Any]:
            """Process single file with appropriate agent."""
            result = await agent.analyze(str(file_path))
            return {
                "file_type": file_type,
                "analysis": result
            }

        # Process files in batches
        type_results = await process_files_in_batches(
            type_files,
            process_file,
            batch_size=batch_size,
            max_concurrency=max_concurrency,
            progress_callback=show_progress
        )

        all_results.extend(type_results)

    # Calculate statistics
    success_count = sum(1 for r in all_results if r.get("success", False))
    error_count = len(all_results) - success_count
    total_cost = sum(
        r.get("result", {}).get("analysis", {}).get("cost", 0.0)
        for r in all_results
        if r.get("success", False)
    )

    # Format summary
    summary = f"""Directory Analysis Complete
{'=' * 60}
Total Files Found: {len(files)}
Successfully Analyzed: {success_count}
Failed: {error_count}
Total Cost: ${total_cost:.4f}

Files by Type:
"""

    for file_type, type_files in files_by_type.items():
        summary += f"  • {file_type}: {len(type_files)} files\n"

    summary = summary.strip()

    return {
        "content": [{
            "type": "text",
            "text": summary
        }],
        "total_files": len(files),
        "success_count": success_count,
        "error_count": error_count,
        "total_cost": total_cost,
        "results": all_results
    }


class ProgressTracker:
    """Track and display progress for long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            description: Description of operation
        """
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = None

    def start(self):
        """Start tracking."""
        import time
        self.start_time = time.time()
        logger.info(f"{self.description}: Starting ({self.total} items)")

    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        if self.current % 10 == 0 or self.current == self.total:
            self._log_progress()

    def _log_progress(self):
        """Log current progress."""
        import time
        if not self.start_time:
            return

        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        items_per_sec = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / items_per_sec if items_per_sec > 0 else 0

        logger.info(
            f"{self.description}: {self.current}/{self.total} "
            f"({percentage:.1f}%) - "
            f"{items_per_sec:.1f} items/sec - "
            f"ETA: {eta:.0f}s"
        )

    def complete(self):
        """Mark as complete."""
        import time
        if not self.start_time:
            return

        elapsed = time.time() - self.start_time
        logger.info(
            f"{self.description}: Complete - "
            f"{self.current}/{self.total} items in {elapsed:.1f}s"
        )
