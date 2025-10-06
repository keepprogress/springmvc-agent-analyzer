"""
SDK Agent Constants.

Centralized constants to avoid magic numbers and improve maintainability.
"""

# File Detection
FILE_DETECTION_BUFFER_SIZE = 1000  # Characters to read for file type detection
FILE_DETECTION_MAX_LINES = 100     # Maximum lines to read for detection

# Context Management
DEFAULT_COMPACT_THRESHOLD = 50     # Compact context after N turns
DEFAULT_KEEP_RECENT = 10          # Keep N recent messages
DEFAULT_MAX_TURNS = 20            # Maximum conversation turns

# Confidence Thresholds
MIN_CONFIDENCE_THRESHOLD = 0.7    # Minimum acceptable confidence
HIGH_CONFIDENCE_THRESHOLD = 0.9   # High confidence threshold
STRUCTURE_VALIDATION_PENALTY = 0.6

# Cache Configuration
DEFAULT_CACHE_DIR = ".cache"
DEFAULT_CACHE_SIZE_MB = 1000
DEFAULT_CACHE_TTL_SECONDS = 86400  # 24 hours
SEMANTIC_SIMILARITY_THRESHOLD = 0.85

# Permission Modes
PERMISSION_MODE_ACCEPT_ALL = "acceptAll"
PERMISSION_MODE_ACCEPT_EDITS = "acceptEdits"
PERMISSION_MODE_REJECT_ALL = "rejectAll"
PERMISSION_MODE_CUSTOM = "custom"

VALID_PERMISSION_MODES = [
    PERMISSION_MODE_ACCEPT_ALL,
    PERMISSION_MODE_ACCEPT_EDITS,
    PERMISSION_MODE_REJECT_ALL,
    PERMISSION_MODE_CUSTOM,
]

# Permission Decisions
PERMISSION_ALLOW = "allow"
PERMISSION_CONFIRM = "confirm"
PERMISSION_DENY = "deny"

VALID_PERMISSION_DECISIONS = [
    PERMISSION_ALLOW,
    PERMISSION_CONFIRM,
    PERMISSION_DENY,
]

# Server Modes
SERVER_MODE_API = "api"
SERVER_MODE_PASSIVE = "passive"
SERVER_MODE_SDK_AGENT = "sdk_agent"

VALID_SERVER_MODES = [
    SERVER_MODE_API,
    SERVER_MODE_PASSIVE,
    SERVER_MODE_SDK_AGENT,
]

# Output Formats
OUTPUT_FORMAT_MARKDOWN = "markdown"
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMAT_HTML = "html"
OUTPUT_FORMAT_TEXT = "text"

VALID_OUTPUT_FORMATS = [
    OUTPUT_FORMAT_MARKDOWN,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_HTML,
    OUTPUT_FORMAT_TEXT,
]

# File Types
FILE_TYPE_CONTROLLER = "controller"
FILE_TYPE_SERVICE = "service"
FILE_TYPE_MAPPER = "mapper"
FILE_TYPE_JSP = "jsp"
FILE_TYPE_PROCEDURE = "procedure"
FILE_TYPE_UNKNOWN = "unknown"

VALID_FILE_TYPES = [
    FILE_TYPE_CONTROLLER,
    FILE_TYPE_SERVICE,
    FILE_TYPE_MAPPER,
    FILE_TYPE_JSP,
    FILE_TYPE_PROCEDURE,
    FILE_TYPE_UNKNOWN,
]

# File Extensions
FILE_EXT_JAVA = ".java"
FILE_EXT_JSP = ".jsp"
FILE_EXT_XML = ".xml"
FILE_EXT_SQL = ".sql"

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/sdk_agent.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Phase Status
PHASE_NOT_IMPLEMENTED_MESSAGE = (
    "This feature is not yet implemented. "
    "Full implementation coming in Phase {phase}. "
    "See docs/SDK_AGENT_IMPLEMENTATION_PLAN.md for details."
)

# Tool Categories
READ_ONLY_TOOLS = {
    "analyze_controller",
    "analyze_service",
    "analyze_mapper",
    "analyze_jsp",
    "analyze_procedure",
    "query_graph",
    "find_dependencies",
    "analyze_impact",
    "list_files",
    "read_file",
}

EDIT_TOOLS = {
    "build_graph",
    "export_graph",
}

ALL_TOOLS = READ_ONLY_TOOLS | EDIT_TOOLS
