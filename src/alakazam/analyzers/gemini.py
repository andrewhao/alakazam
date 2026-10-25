"""Backward compatibility wrapper for Gemini document analyzer.

Shifted to Antigravity CLI ('agy') analyzer.
"""

from alakazam.analyzers.antigravity import AntigravityAnalyzer

# Backwards compatibility alias
GeminiAnalyzer = AntigravityAnalyzer

__all__ = ["GeminiAnalyzer", "AntigravityAnalyzer"]
