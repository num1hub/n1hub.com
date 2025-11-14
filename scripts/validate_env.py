#!/usr/bin/env python3
"""
Environment Variable Validator for N1Hub v0.1

Validates required and optional environment variables for both frontend and backend.
"""

import os
import re
import sys
from typing import Dict, List, Tuple
from urllib.parse import urlparse


class EnvValidator:
    """Validates environment variables for N1Hub v0.1 deployment."""

    def __init__(self, target: str = "all"):
        """
        Initialize validator.
        
        Args:
            target: "frontend", "backend", or "all"
        """
        self.target = target
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_database_url(self, value: str) -> bool:
        """Validate PostgreSQL DATABASE_URL format."""
        if not value:
            return False
        try:
            parsed = urlparse(value)
            if parsed.scheme not in ["postgresql", "postgres"]:
                return False
            if not parsed.hostname:
                return False
            return True
        except Exception:
            return False
    
    def validate_redis_url(self, value: str) -> bool:
        """Validate Redis URL format."""
        if not value:
            return False
        try:
            parsed = urlparse(value)
            if parsed.scheme not in ["redis", "rediss"]:
                return False
            return True
        except Exception:
            return False
    
    def validate_url(self, value: str) -> bool:
        """Validate generic URL format."""
        if not value:
            return False
        try:
            parsed = urlparse(value)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def validate_backend(self) -> None:
        """Validate backend environment variables."""
        # Required backend variables
        required_backend = {
            "N1HUB_POSTGRES_DSN": {
                "description": "PostgreSQL connection string",
                "validator": self.validate_database_url,
                "example": "postgresql://user:pass@host:5432/dbname"
            },
        }
        
        # Optional but recommended
        optional_backend = {
            "N1HUB_REDIS_URL": {
                "description": "Redis connection URL (optional, falls back to in-memory)",
                "validator": self.validate_redis_url,
                "example": "redis://localhost:6379/0"
            },
            "N1HUB_LLM_PROVIDER": {
                "description": "LLM provider: 'anthropic' or 'openai'",
                "validator": lambda v: v in ["anthropic", "openai"],
                "example": "anthropic"
            },
            "N1HUB_LLM_API_KEY": {
                "description": "LLM API key (required if using LLM features)",
                "validator": lambda v: bool(v and len(v) > 10),
                "example": "sk-..."
            },
            "N1HUB_LLM_MODEL": {
                "description": "LLM model name",
                "validator": lambda v: bool(v),
                "example": "claude-3-haiku-20240307"
            },
        }
        
        print("=" * 60)
        print("Backend Environment Variables")
        print("=" * 60)
        
        # Check required variables
        for var, config in required_backend.items():
            value = os.getenv(var, "")
            if not value:
                self.errors.append(f"Missing required: {var} - {config['description']}")
                print(f"✗ {var}: MISSING (required)")
                print(f"  Example: {config['example']}")
            elif not config['validator'](value):
                self.errors.append(f"Invalid format: {var}")
                print(f"✗ {var}: INVALID FORMAT")
                print(f"  Current: {value[:50]}...")
                print(f"  Expected: {config['example']}")
            else:
                # Mask sensitive values
                display_value = value
                if "password" in var.lower() or "key" in var.lower() or "secret" in var.lower():
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✓ {var}: {display_value}")
        
        # Check optional variables
        for var, config in optional_backend.items():
            value = os.getenv(var, "")
            if not value:
                self.warnings.append(f"Optional: {var} - {config['description']}")
                print(f"⚠ {var}: NOT SET (optional)")
                if var == "N1HUB_LLM_API_KEY":
                    print(f"  Note: LLM features will be disabled without this")
            elif not config['validator'](value):
                self.warnings.append(f"Invalid format: {var}")
                print(f"⚠ {var}: INVALID FORMAT")
                print(f"  Expected: {config['example']}")
            else:
                display_value = value[:20] + "..." if len(value) > 20 else value
                if "key" in var.lower() or "secret" in var.lower():
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✓ {var}: {display_value}")
        
        print()
    
    def validate_frontend(self) -> None:
        """Validate frontend environment variables."""
        # Required frontend variables
        required_frontend = {
            "NEXT_PUBLIC_API_URL": {
                "description": "Backend API base URL",
                "validator": self.validate_url,
                "example": "https://api.n1hub.com"
            },
        }
        
        # Optional frontend variables
        optional_frontend = {
            "NEXT_PUBLIC_SSE_URL": {
                "description": "SSE events URL (defaults to /api/events)",
                "validator": self.validate_url,
                "example": "https://api.n1hub.com"
            },
            "ENGINE_BASE_URL": {
                "description": "Backend engine URL (server-side only)",
                "validator": self.validate_url,
                "example": "https://api.n1hub.com"
            },
        }
        
        print("=" * 60)
        print("Frontend Environment Variables")
        print("=" * 60)
        
        # Check required variables
        for var, config in required_frontend.items():
            value = os.getenv(var, "")
            if not value:
                self.errors.append(f"Missing required: {var} - {config['description']}")
                print(f"✗ {var}: MISSING (required)")
                print(f"  Example: {config['example']}")
            elif not config['validator'](value):
                self.errors.append(f"Invalid format: {var}")
                print(f"✗ {var}: INVALID FORMAT")
                print(f"  Current: {value}")
                print(f"  Expected: {config['example']}")
            else:
                print(f"✓ {var}: {value}")
        
        # Check optional variables
        for var, config in optional_frontend.items():
            value = os.getenv(var, "")
            if not value:
                print(f"⚠ {var}: NOT SET (optional)")
                print(f"  Note: {config['description']}")
            elif not config['validator'](value):
                self.warnings.append(f"Invalid format: {var}")
                print(f"⚠ {var}: INVALID FORMAT")
                print(f"  Expected: {config['example']}")
            else:
                print(f"✓ {var}: {value}")
        
        print()
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run validation.
        
        Returns:
            (is_valid, errors, warnings)
        """
        if self.target in ["all", "backend"]:
            self.validate_backend()
        
        if self.target in ["all", "frontend"]:
            self.validate_frontend()
        
        # Summary
        print("=" * 60)
        print("Validation Summary")
        print("=" * 60)
        
        if self.errors:
            print(f"✗ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✓ No errors found")
        
        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate N1Hub v0.1 environment variables"
    )
    parser.add_argument(
        "--target",
        choices=["frontend", "backend", "all"],
        default="all",
        help="Target to validate (default: all)"
    )
    parser.add_argument(
        "--env-file",
        help="Load environment variables from file (e.g., .env.production)"
    )
    
    args = parser.parse_args()
    
    # Load environment file if provided
    if args.env_file and os.path.exists(args.env_file):
        print(f"Loading environment from: {args.env_file}")
        with open(args.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key.strip()] = value
        print()
    
    validator = EnvValidator(target=args.target)
    is_valid, errors, warnings = validator.validate()
    
    if not is_valid:
        print("\n" + "=" * 60)
        print("Validation FAILED")
        print("=" * 60)
        print("\nPlease fix the errors above before deploying.")
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("Validation PASSED")
        print("=" * 60)
        if warnings:
            print("\nNote: Some optional variables are not set. This is OK for basic functionality.")
        sys.exit(0)


if __name__ == "__main__":
    main()
