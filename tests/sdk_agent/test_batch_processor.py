"""
Unit Tests for SDK Agent Batch Processor.

Tests batch processing, concurrency control, and progress tracking for
efficient large-scale file analysis.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import time

from sdk_agent.tools.batch_processor import (
    process_files_in_batches,
    analyze_directory_optimized,
    ProgressTracker
)


class TestProcessFilesInBatches:
    """Test batch file processing with concurrency control."""

    @pytest.mark.asyncio
    async def test_basic_batch_processing(self):
        """Test basic batch processing functionality."""
        files = [Path(f"file{i}.java") for i in range(10)]
        processed = []

        async def mock_process(file_path: Path):
            processed.append(str(file_path))
            await asyncio.sleep(0.01)  # Simulate work
            return {"file": str(file_path), "analyzed": True}

        results = await process_files_in_batches(
            files,
            mock_process,
            batch_size=5,
            max_concurrency=3
        )

        assert len(results) == 10
        assert all(r.get("success") for r in results)
        assert len(processed) == 10

    @pytest.mark.asyncio
    async def test_batch_size_respected(self):
        """Test that files are processed in correct batch sizes."""
        files = [Path(f"file{i}.java") for i in range(25)]
        batches_seen = []

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.001)
            return {"file": str(file_path)}

        # Track batch boundaries
        original_gather = asyncio.gather

        async def tracking_gather(*args, **kwargs):
            batches_seen.append(len(args))
            return await original_gather(*args, **kwargs)

        with patch('asyncio.gather', side_effect=tracking_gather):
            await process_files_in_batches(
                files,
                mock_process,
                batch_size=10,
                max_concurrency=5
            )

        # Should have 3 batches: 10, 10, 5
        assert len(batches_seen) == 3
        assert batches_seen == [10, 10, 5]

    @pytest.mark.asyncio
    async def test_concurrency_control(self):
        """Test that max concurrency is enforced."""
        files = [Path(f"file{i}.java") for i in range(20)]
        concurrent_count = 0
        max_concurrent = 0

        async def mock_process(file_path: Path):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return {"file": str(file_path)}

        await process_files_in_batches(
            files,
            mock_process,
            batch_size=20,  # All in one batch
            max_concurrency=5
        )

        # Should never exceed max_concurrency
        assert max_concurrent <= 5

    @pytest.mark.asyncio
    async def test_error_handling_in_batch(self):
        """Test that errors in individual files don't stop batch."""
        files = [Path(f"file{i}.java") for i in range(10)]

        async def mock_process(file_path: Path):
            if "file5" in str(file_path):
                raise ValueError("Simulated error")
            return {"file": str(file_path), "analyzed": True}

        results = await process_files_in_batches(
            files,
            mock_process,
            batch_size=5,
            max_concurrency=3
        )

        # Should have 10 results (including the error)
        assert len(results) == 10

        # 9 should be successful, 1 should be error
        successful = [r for r in results if r.get("success")]
        errors = [r for r in results if not r.get("success")]

        assert len(successful) == 9
        assert len(errors) == 1
        assert "error" in errors[0]

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test that progress callback is called correctly."""
        files = [Path(f"file{i}.java") for i in range(20)]
        progress_updates = []

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.001)
            return {"file": str(file_path)}

        def progress_callback(progress):
            progress_updates.append(progress)

        await process_files_in_batches(
            files,
            mock_process,
            batch_size=5,
            max_concurrency=3,
            progress_callback=progress_callback
        )

        # Should have 4 progress updates (4 batches)
        assert len(progress_updates) == 4

        # Each update should have required fields
        for update in progress_updates:
            assert "batch" in update
            assert "total_batches" in update
            assert "processed" in update
            assert "total" in update
            assert "success_count" in update
            assert "error_count" in update

        # Final update should show all files processed
        final_update = progress_updates[-1]
        assert final_update["processed"] == 20
        assert final_update["total"] == 20

    @pytest.mark.asyncio
    async def test_empty_file_list(self):
        """Test handling of empty file list."""
        async def mock_process(file_path: Path):
            return {"file": str(file_path)}

        results = await process_files_in_batches(
            [],
            mock_process,
            batch_size=5,
            max_concurrency=3
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_single_file(self):
        """Test processing single file."""
        files = [Path("single.java")]

        async def mock_process(file_path: Path):
            return {"file": str(file_path), "analyzed": True}

        results = await process_files_in_batches(
            files,
            mock_process,
            batch_size=10,
            max_concurrency=5
        )

        assert len(results) == 1
        assert results[0].get("success") is True


class TestAnalyzeDirectoryOptimized:
    """Test optimized directory analysis."""

    @pytest.mark.asyncio
    async def test_directory_analysis_basic(self, tmp_path):
        """Test basic directory analysis."""
        # Create test files
        (tmp_path / "Controller1.java").write_text("controller")
        (tmp_path / "Controller2.java").write_text("controller")
        (tmp_path / "Service1.java").write_text("service")

        # Mock file type detector
        def file_type_detector(path: str):
            if "Controller" in path:
                return "controller"
            elif "Service" in path:
                return "service"
            return None

        # Mock agent getter
        mock_agent = Mock()
        mock_agent.analyze = AsyncMock(return_value={"analyzed": True})

        def agent_getter(file_type):
            return mock_agent

        result = await analyze_directory_optimized(
            directory=tmp_path,
            pattern="*.java",
            recursive=False,
            file_type_detector=file_type_detector,
            agent_getter=agent_getter,
            batch_size=10,
            max_concurrency=5
        )

        # Should have processed all files
        assert result["total_files"] == 3
        assert result["success_count"] >= 0
        assert "results" in result

    @pytest.mark.asyncio
    async def test_recursive_directory_search(self, tmp_path):
        """Test recursive directory scanning."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "controllers").mkdir()
        (tmp_path / "src" / "controllers" / "User.java").write_text("controller")
        (tmp_path / "src" / "services").mkdir()
        (tmp_path / "src" / "services" / "User.java").write_text("service")

        def file_type_detector(path: str):
            return "java"

        mock_agent = Mock()
        mock_agent.analyze = AsyncMock(return_value={"analyzed": True})

        def agent_getter(file_type):
            return mock_agent

        result = await analyze_directory_optimized(
            directory=tmp_path,
            pattern="**/*.java",
            recursive=True,
            file_type_detector=file_type_detector,
            agent_getter=agent_getter
        )

        # Should find files in subdirectories
        assert result["total_files"] == 2

    @pytest.mark.asyncio
    async def test_no_files_found(self, tmp_path):
        """Test handling when no files match pattern."""
        def file_type_detector(path: str):
            return "java"

        def agent_getter(file_type):
            return Mock()

        result = await analyze_directory_optimized(
            directory=tmp_path,
            pattern="*.java",
            recursive=False,
            file_type_detector=file_type_detector,
            agent_getter=agent_getter
        )

        assert result["total_files"] == 0
        assert "No files found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_file_grouping_by_type(self, tmp_path):
        """Test that files are grouped by type for processing."""
        # Create mixed file types
        for i in range(3):
            (tmp_path / f"Controller{i}.java").write_text("controller")
            (tmp_path / f"Service{i}.java").write_text("service")

        agent_calls = {}

        def file_type_detector(path: str):
            if "Controller" in path:
                return "controller"
            elif "Service" in path:
                return "service"
            return None

        def agent_getter(file_type):
            if file_type not in agent_calls:
                agent_calls[file_type] = 0

            mock_agent = Mock()

            async def track_analyze(path):
                agent_calls[file_type] += 1
                return {"analyzed": True}

            mock_agent.analyze = track_analyze
            return mock_agent

        await analyze_directory_optimized(
            directory=tmp_path,
            pattern="*.java",
            recursive=False,
            file_type_detector=file_type_detector,
            agent_getter=agent_getter
        )

        # Should have called agent for each file type
        assert "controller" in agent_calls
        assert "service" in agent_calls
        assert agent_calls["controller"] == 3
        assert agent_calls["service"] == 3


class TestProgressTracker:
    """Test progress tracking functionality."""

    def test_progress_tracker_creation(self):
        """Test creating progress tracker."""
        tracker = ProgressTracker(total=100, description="Testing")

        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.description == "Testing"
        assert tracker.start_time is None

    def test_progress_tracker_start(self):
        """Test starting progress tracking."""
        tracker = ProgressTracker(total=100)
        tracker.start()

        assert tracker.start_time is not None

    def test_progress_tracker_update(self):
        """Test updating progress."""
        tracker = ProgressTracker(total=100)
        tracker.start()

        tracker.update(10)
        assert tracker.current == 10

        tracker.update(5)
        assert tracker.current == 15

    @patch('sdk_agent.tools.batch_processor.logger')
    def test_progress_logging(self, mock_logger):
        """Test that progress is logged at intervals."""
        tracker = ProgressTracker(total=100, description="Testing")
        tracker.start()

        # Update by 10 (should log)
        tracker.update(10)
        assert mock_logger.info.called

        # Reset mock
        mock_logger.reset_mock()

        # Update by 5 (should not log - not at 10-interval)
        tracker.update(5)
        assert not mock_logger.info.called

        # Update to 20 total (should log)
        tracker.update(5)
        assert mock_logger.info.called

    def test_progress_complete(self):
        """Test marking progress as complete."""
        tracker = ProgressTracker(total=100)
        tracker.start()
        tracker.update(100)

        with patch('sdk_agent.tools.batch_processor.logger') as mock_logger:
            tracker.complete()
            assert mock_logger.info.called

            log_message = mock_logger.info.call_args[0][0]
            assert "Complete" in log_message
            assert "100/100" in log_message

    def test_progress_without_start(self):
        """Test that logging handles missing start time."""
        tracker = ProgressTracker(total=100)
        # Don't call start()

        with patch('sdk_agent.tools.batch_processor.logger') as mock_logger:
            tracker.update(10)
            tracker.complete()
            # Should not crash even without start_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
