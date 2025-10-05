"""
Semantic Cache Manager for LLM analysis results.

This module provides caching functionality to avoid redundant LLM queries.
Uses file content hashing for cache keys to handle minor code changes.
Future enhancement: semantic similarity for true semantic caching.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import hashlib
import json
import pickle
from pathlib import Path
import logging
import time
from datetime import timedelta


class CacheManager:
    """
    Semantic cache for LLM analysis results.

    Strategy:
    - Level 1: Exact hash match (instant lookup)
    - Level 2: Semantic similarity (future: vector embeddings)

    Expected Hit Rate: 60-80%

    Attributes:
        cache_dir: Directory for cache files
        ttl_days: Time-to-live for cache entries in days
        max_cache_size: Maximum number of cache entries
        stats: Cache statistics (hits, misses, saves)
        logger: Logger instance
    """

    def __init__(
        self,
        cache_dir: str = ".cache",
        ttl_days: int = 30,
        max_cache_size: int = 10000
    ):
        """
        Initialize the Cache Manager.

        Args:
            cache_dir: Directory to store cache files
            ttl_days: Cache entry time-to-live in days
            max_cache_size: Maximum number of cached entries
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.ttl_days = ttl_days
        self.max_cache_size = max_cache_size
        self.logger = logging.getLogger("core.cache_manager")

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictions": 0
        }

        self.logger.info(
            f"CacheManager initialized: dir={cache_dir}, ttl={ttl_days}d, "
            f"max_size={max_cache_size}"
        )

    def get(
        self,
        agent_name: str,
        file_path: str,
        file_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result.

        Args:
            agent_name: Name of the agent that analyzed this
            file_path: Path to the file
            file_content: Current file content

        Returns:
            Cached result dictionary or None if cache miss
        """
        cache_key = self._compute_cache_key(agent_name, file_path, file_content)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        # Check if cache file exists
        if not cache_file.exists():
            self.stats["misses"] += 1
            self.logger.debug(f"Cache MISS: {file_path} (key={cache_key[:8]}...)")
            return None

        # Check if cache is expired
        if self._is_expired(cache_file):
            self.logger.debug(f"Cache EXPIRED: {cache_file}")
            try:
                cache_file.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to delete expired cache: {e}")

            self.stats["misses"] += 1
            return None

        # Load cached result
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)

            self.stats["hits"] += 1
            self.logger.info(f"Cache HIT: {file_path} (key={cache_key[:8]}...)")
            return result

        except Exception as e:
            self.logger.error(f"Cache read error for {cache_file}: {e}")
            # Delete corrupted cache file
            try:
                cache_file.unlink()
            except Exception:
                pass

            self.stats["misses"] += 1
            return None

    def save(
        self,
        agent_name: str,
        file_path: str,
        file_content: str,
        result: Dict[str, Any]
    ):
        """
        Save analysis result to cache.

        Args:
            agent_name: Name of the agent
            file_path: Path to the file
            file_content: File content
            result: Analysis result to cache
        """
        # Check cache size and evict if needed
        self._enforce_cache_size_limit()

        cache_key = self._compute_cache_key(agent_name, file_path, file_content)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            self.stats["saves"] += 1
            self.logger.debug(f"Cache SAVE: {file_path} (key={cache_key[:8]}...)")

        except Exception as e:
            self.logger.error(f"Cache write error for {cache_file}: {e}")

    def _compute_cache_key(
        self,
        agent_name: str,
        file_path: str,
        file_content: str
    ) -> str:
        """
        Compute cache key from agent + file + content hash.

        Future enhancement: Use semantic embeddings instead of raw content hash
        for true semantic similarity matching.

        Args:
            agent_name: Name of the agent
            file_path: Path to the file
            file_content: File content

        Returns:
            Cache key (16-char hex string)
        """
        # Hash the file content
        content_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()

        # Combine agent name, file path, and content hash
        combined = f"{agent_name}:{file_path}:{content_hash}"

        # Hash the combined string
        cache_key = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        # Return first 16 characters for readability
        return cache_key[:16]

    def _is_expired(self, cache_file: Path) -> bool:
        """
        Check if cache file is older than TTL.

        Args:
            cache_file: Path to cache file

        Returns:
            True if expired, False otherwise
        """
        try:
            file_age_seconds = time.time() - cache_file.stat().st_mtime
            ttl_seconds = timedelta(days=self.ttl_days).total_seconds()

            return file_age_seconds > ttl_seconds

        except Exception as e:
            self.logger.warning(f"Error checking cache expiry for {cache_file}: {e}")
            return True  # Treat as expired if we can't check

    def _enforce_cache_size_limit(self):
        """
        Enforce maximum cache size by evicting oldest entries.

        Uses LRU (Least Recently Used) eviction strategy.
        """
        cache_files = list(self.cache_dir.glob("*.pkl"))

        if len(cache_files) >= self.max_cache_size:
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda f: f.stat().st_mtime)

            # Calculate how many to evict (evict 10% to avoid frequent evictions)
            num_to_evict = max(1, int(self.max_cache_size * 0.1))

            self.logger.info(
                f"Cache size limit reached ({len(cache_files)} >= {self.max_cache_size}), "
                f"evicting {num_to_evict} oldest entries"
            )

            # Evict oldest files
            for cache_file in cache_files[:num_to_evict]:
                try:
                    cache_file.unlink()
                    self.stats["evictions"] += 1
                except Exception as e:
                    self.logger.warning(f"Failed to evict {cache_file}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            {
                "hits": int,
                "misses": int,
                "saves": int,
                "evictions": int,
                "hit_rate": float,
                "cache_files": int,
                "cache_size_mb": float
            }
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0

        # Calculate cache size
        cache_files = list(self.cache_dir.glob("*.pkl"))
        cache_size_bytes = sum(f.stat().st_size for f in cache_files)
        cache_size_mb = cache_size_bytes / (1024 * 1024)

        return {
            **self.stats,
            "hit_rate": round(hit_rate, 3),
            "cache_files": len(cache_files),
            "cache_size_mb": round(cache_size_mb, 2)
        }

    def clear(self, older_than_days: Optional[int] = None):
        """
        Clear cache files.

        Args:
            older_than_days: If specified, only clear files older than this many days.
                           If None, clear all cache files.
        """
        cache_files = list(self.cache_dir.glob("*.pkl"))
        deleted_count = 0

        if older_than_days is None:
            # Clear all
            for cache_file in cache_files:
                try:
                    cache_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {cache_file}: {e}")

            self.logger.info(f"Cleared all cache: deleted {deleted_count} files")

        else:
            # Clear only old files
            cutoff_seconds = timedelta(days=older_than_days).total_seconds()
            current_time = time.time()

            for cache_file in cache_files:
                try:
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > cutoff_seconds:
                        cache_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {cache_file}: {e}")

            self.logger.info(
                f"Cleared cache older than {older_than_days} days: "
                f"deleted {deleted_count} files"
            )

        # Reset stats if clearing all
        if older_than_days is None:
            self.stats = {
                "hits": 0,
                "misses": 0,
                "saves": 0,
                "evictions": 0
            }

    def print_stats(self):
        """Print formatted cache statistics to console."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("📦 CACHE STATISTICS")
        print("=" * 60)
        print(f"Cache Hits:     {stats['hits']}")
        print(f"Cache Misses:   {stats['misses']}")
        print(f"Hit Rate:       {stats['hit_rate']*100:.1f}%")
        print(f"Cache Saves:    {stats['saves']}")
        print(f"Evictions:      {stats['evictions']}")
        print(f"\nCache Files:    {stats['cache_files']}")
        print(f"Cache Size:     {stats['cache_size_mb']:.2f} MB")
        print(f"Max Size:       {self.max_cache_size} files")
        print(f"TTL:            {self.ttl_days} days")
        print("=" * 60 + "\n")

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        stats = self.get_stats()
        return (
            f"<CacheManager(dir='{self.cache_dir}', "
            f"files={stats['cache_files']}, "
            f"hit_rate={stats['hit_rate']:.2f})>"
        )
