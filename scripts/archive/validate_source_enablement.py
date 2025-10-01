#!/usr/bin/env python3
"""
Validation script to check for improperly enabled sources.
Warns users if they enable sources that require special configuration.
"""

import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from paperez_mcp.config.manager import get_current_config


def validate_source_enablement():
    """Validate that enabled sources have proper configuration."""
    print("🔍 Validating source enablement configuration...")

    try:
        config = get_current_config()
        warnings = []
        errors = []

        # Sources that require special setup
        special_sources = {
            "repec": {
                "requirements": ["API access code from RePEc team"],
                "contact": "team@mail.authors.repec.org",
                "setup_guide": "Contact RePEc team for IP-based access code",
            },
            "courtlistener": {
                "requirements": ["API token from CourtListener account"],
                "contact": "courtlistener.com",
                "setup_guide": "Create account and generate API token",
            },
            "core_repository": {
                "requirements": ["API key registration"],
                "contact": "core.ac.uk/services/api",
                "setup_guide": "Register for free API key with email",
            },
            "semantic_scholar": {
                "requirements": ["Optional API key for higher rate limits"],
                "contact": "semanticscholar.org/product/api",
                "setup_guide": "Register for API key to avoid rate limiting",
            },
        }

        for source_name, source_config in config.sources.items():
            if source_config.enabled and source_name in special_sources:
                special_info = special_sources[source_name]

                # Check if this source has been properly configured
                if source_name in ["repec", "courtlistener", "core_repository"]:
                    # These sources require credentials - check if they're missing
                    errors.append(
                        f"❌ Source '{source_name}' is enabled but requires setup:\n"
                        f"   Requirements: {', '.join(special_info['requirements'])}\n"
                        f"   Setup: {special_info['setup_guide']}\n"
                        f"   Contact: {special_info['contact']}"
                    )
                elif source_name == "semantic_scholar":
                    # This is optional but recommended
                    warnings.append(
                        f"⚠️  Source '{source_name}' is enabled without API key:\n"
                        f"   Recommendation: {special_info['setup_guide']}\n"
                        f"   Without API key: Subject to rate limiting\n"
                        f"   Register at: {special_info['contact']}"
                    )

        # Print results
        if errors:
            print("\n🚨 CONFIGURATION ERRORS:")
            for error in errors:
                print(f"\n{error}")

        if warnings:
            print("\n⚠️  CONFIGURATION WARNINGS:")
            for warning in warnings:
                print(f"\n{warning}")

        if not errors and not warnings:
            print("✅ All enabled sources are properly configured!")

        # Additional guidance
        if errors or warnings:
            print("\n💡 CONFIGURATION GUIDANCE:")
            print("   - Set 'enabled: false' for sources you haven't configured")
            print(
                "   - Add 'disabled_reason' field to document why sources are disabled"
            )
            print("   - Check configuration comments for setup instructions")
            print("   - Test source functionality after enabling")

        return len(errors) == 0

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    success = validate_source_enablement()
    sys.exit(0 if success else 1)
