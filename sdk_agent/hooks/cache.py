"""Cache Hook for SDK Agent Mode - Caches analysis results."""

from typing import Dict, Any, Optional
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("sdk_agent.hooks.cache")


class CacheHook:
    """Post-tool hook for caching analysis results."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.cache_dir = Path(self.config.get("cache_dir", ".cache/sdk_agent"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CacheHook initialized (cache_dir={self.cache_dir})")

    async def __call__(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Cache tool results."""
        if not self.enabled or tool_output.get("is_error"):
            return {}

        try:
            if tool_name.startswith("analyze_"):
                self._cache_analysis_result(tool_name, tool_input, tool_output)
        except Exception as e:
            logger.error(f"Cache error: {e}")

        return {}

    def _cache_analysis_result(self, tool_name: str, tool_input: Dict[str, Any], tool_output: Dict[str, Any]):
        """Cache analysis result to disk."""
        file_path = tool_input.get("file_path")
        if not file_path:
            return

        cache_file = self.cache_dir / f"{tool_name}_{Path(file_path).name}.json"
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output
        }
        cache_file.write_text(json.dumps(cache_data, indent=2))
        logger.debug(f"Cached result: {cache_file}")


default_cache_hook = CacheHook()
