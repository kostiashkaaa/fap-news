#!/usr/bin/env python3
"""
FAP News - Configuration Module
Centralized configuration management with async support
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)

# Default paths
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"


@dataclass
class TelegramConfig:
    """Telegram configuration"""
    token: str = ""
    channel_id: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelegramConfig":
        return cls(
            token=data.get("token", "") or os.getenv("TELEGRAM_BOT_TOKEN", ""),
            channel_id=data.get("channel_id", "")
        )


@dataclass
class SourceConfig:
    """News source configuration"""
    name: str
    tag: str
    rss: str = ""
    html_url: str = ""
    html_selector: Dict[str, str] = field(default_factory=dict)
    priority: int = 2  # 1=low, 2=medium, 3=high
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        return cls(
            name=data.get("name", "Unknown"),
            tag=data.get("tag", ""),
            rss=data.get("rss", ""),
            html_url=data.get("html_url", ""),
            html_selector=data.get("html_selector", {}),
            priority=data.get("priority", 2)
        )


@dataclass
class FiltersConfig:
    """Filters configuration"""
    include_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    max_age_hours: int = 24
    max_age_minutes: Optional[int] = 120
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FiltersConfig":
        return cls(
            include_keywords=data.get("include_keywords", []),
            exclude_keywords=data.get("exclude_keywords", []),
            max_age_hours=data.get("max_age_hours", 24),
            max_age_minutes=data.get("max_age_minutes")
        )


@dataclass
class SchedulerConfig:
    """Scheduler configuration"""
    interval_minutes: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulerConfig":
        return cls(interval_minutes=data.get("interval_minutes", 10))


@dataclass
class PostingConfig:
    """Posting configuration"""
    min_delay_minutes: int = 1
    max_delay_minutes: int = 4
    max_queue_size: int = 50
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostingConfig":
        return cls(
            min_delay_minutes=data.get("min_delay_minutes", 1),
            max_delay_minutes=data.get("max_delay_minutes", 4),
            max_queue_size=data.get("max_queue_size", 50)
        )


@dataclass
class RateLimitConfig:
    """Rate limit configuration for AI"""
    max_urgency_checks: int = 8
    max_freshness_checks: int = 10
    delay_between_calls: float = 0.8
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RateLimitConfig":
        return cls(
            max_urgency_checks=data.get("max_urgency_checks", 8),
            max_freshness_checks=data.get("max_freshness_checks", 10),
            delay_between_calls=data.get("delay_between_calls", 0.8)
        )


@dataclass
class AISummarizationConfig:
    """AI summarization configuration"""
    enabled: bool = False
    provider: str = "groq"
    api_key: str = ""
    model: str = "llama-3.1-8b-instant"
    max_summary_length: int = 500
    temperature: float = 0.2
    max_tokens: int = 1024
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AISummarizationConfig":
        return cls(
            enabled=data.get("enabled", False),
            provider=data.get("provider", "groq"),
            api_key=data.get("api_key", "") or os.getenv("GROQ_API_KEY", ""),
            model=data.get("model", "llama-3.1-8b-instant"),
            max_summary_length=data.get("max_summary_length", 500),
            temperature=data.get("temperature", 0.2),
            max_tokens=data.get("max_tokens", 1024),
            cache_enabled=data.get("cache_enabled", True),
            cache_ttl_hours=data.get("cache_ttl_hours", 24),
            rate_limit=RateLimitConfig.from_dict(data.get("rate_limit", {}))
        )


@dataclass
class DeduplicationConfig:
    """Deduplication configuration"""
    enabled: bool = True
    similarity_threshold: float = 0.7
    title_weight: float = 0.6
    content_weight: float = 0.4
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeduplicationConfig":
        return cls(
            enabled=data.get("enabled", True),
            similarity_threshold=data.get("similarity_threshold", 0.7),
            title_weight=data.get("title_weight", 0.6),
            content_weight=data.get("content_weight", 0.4)
        )


@dataclass 
class SourcePriorityConfig:
    """Source priority configuration"""
    high_priority: List[str] = field(default_factory=list)
    medium_priority: List[str] = field(default_factory=list)
    low_priority: List[str] = field(default_factory=list)
    max_sources_per_cycle: int = 3
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourcePriorityConfig":
        return cls(
            high_priority=data.get("high_priority", [
                "Fox News", "New York Times World", "Financial Times World",
                "Washington Post World", "The Guardian World", "BBC News Russian",
                "Euronews", "Deutsche Welle", "France 24", "Al Jazeera"
            ]),
            medium_priority=data.get("medium_priority", [
                "South China Morning Post", "Japan Times", "Reuters - World News"
            ]),
            low_priority=data.get("low_priority", [
                "RT Russian", "TASS", "RIA Novosti", "Lenta.ru"
            ]),
            max_sources_per_cycle=data.get("max_sources_per_cycle", 3)
        )


@dataclass
class AdminConfig:
    """Admin configuration"""
    allowed_user_ids: List[int] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminConfig":
        return cls(allowed_user_ids=data.get("allowed_user_ids", []))


@dataclass
class AppConfig:
    """Main application configuration"""
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    sources: List[SourceConfig] = field(default_factory=list)
    filters: FiltersConfig = field(default_factory=FiltersConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    posting: PostingConfig = field(default_factory=PostingConfig)
    ai_summarization: AISummarizationConfig = field(default_factory=AISummarizationConfig)
    deduplication: DeduplicationConfig = field(default_factory=DeduplicationConfig)
    source_priority: SourcePriorityConfig = field(default_factory=SourcePriorityConfig)
    admin: AdminConfig = field(default_factory=AdminConfig)
    
    # Raw config for backwards compatibility
    _raw: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        sources = [SourceConfig.from_dict(s) for s in data.get("sources", [])]
        
        return cls(
            telegram=TelegramConfig.from_dict(data.get("telegram", {})),
            sources=sources,
            filters=FiltersConfig.from_dict(data.get("filters", {})),
            scheduler=SchedulerConfig.from_dict(data.get("scheduler", {})),
            posting=PostingConfig.from_dict(data.get("posting", {})),
            ai_summarization=AISummarizationConfig.from_dict(data.get("ai_summarization", {})),
            deduplication=DeduplicationConfig.from_dict(data.get("deduplication", {})),
            source_priority=SourcePriorityConfig.from_dict(data.get("source_priority", {})),
            admin=AdminConfig.from_dict(data.get("admin", {})),
            _raw=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config back to dictionary for saving"""
        return self._raw
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get raw config value for backwards compatibility"""
        return self._raw.get(key, default)


class ConfigManager:
    """Configuration manager with caching and async support"""
    
    _instance: Optional["ConfigManager"] = None
    _config: Optional[AppConfig] = None
    _config_path: Path = CONFIG_PATH
    _last_modified: float = 0
    
    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (useful for testing)"""
        cls._instance = None
        cls._config = None
    
    def _check_reload(self) -> bool:
        """Check if config file was modified"""
        try:
            current_mtime = self._config_path.stat().st_mtime
            if current_mtime > self._last_modified:
                self._last_modified = current_mtime
                return True
        except FileNotFoundError:
            pass
        return False
    
    def load_config(self, force_reload: bool = False) -> AppConfig:
        """
        Load configuration from JSON file with caching
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            AppConfig instance
        """
        if self._config is not None and not force_reload and not self._check_reload():
            return self._config
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._config = AppConfig.from_dict(data)
            self._last_modified = self._config_path.stat().st_mtime
            logger.debug("Configuration loaded successfully")
            return self._config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self._config_path}")
            raise RuntimeError(f"Config file not found at {self._config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise RuntimeError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def load_raw_config(self) -> Dict[str, Any]:
        """Load raw configuration dictionary (for backwards compatibility)"""
        config = self.load_config()
        return config._raw
    
    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """
        Save configuration to JSON file
        
        Args:
            config: Config to save, uses current if not provided
        """
        if config is None:
            config = self._config
        
        if config is None:
            raise RuntimeError("No configuration to save")
        
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._last_modified = self._config_path.stat().st_mtime
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def save_raw_config(self, data: Dict[str, Any]) -> None:
        """Save raw configuration dictionary"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Invalidate cache
            self._config = None
            self._last_modified = self._config_path.stat().st_mtime
            logger.info("Raw configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving raw config: {e}")
            raise
    
    def update_sources(self, sources: List[Dict[str, Any]]) -> None:
        """Update sources in configuration"""
        config = self.load_config()
        config._raw["sources"] = sources
        self.save_raw_config(config._raw)
    
    def add_source(self, source: Dict[str, Any]) -> None:
        """Add a new source to configuration"""
        config = self.load_config()
        sources = config._raw.get("sources", [])
        sources.append(source)
        config._raw["sources"] = sources
        self.save_raw_config(config._raw)
    
    def remove_source(self, index: int) -> Optional[Dict[str, Any]]:
        """Remove a source by index"""
        config = self.load_config()
        sources = config._raw.get("sources", [])
        
        if 0 <= index < len(sources):
            removed = sources.pop(index)
            config._raw["sources"] = sources
            self.save_raw_config(config._raw)
            return removed
        return None


# Convenience functions for backwards compatibility
def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file
    
    Args:
        path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return ConfigManager.get_instance().load_raw_config()


def save_config(config: Dict[str, Any], path: Optional[str] = None) -> None:
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        path: Optional path to config file
    """
    if path:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    else:
        ConfigManager.get_instance().save_raw_config(config)


def get_config() -> AppConfig:
    """Get typed configuration"""
    return ConfigManager.get_instance().load_config()


def get_config_manager() -> ConfigManager:
    """Get configuration manager instance"""
    return ConfigManager.get_instance()
