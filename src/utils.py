"""
Utility functions for API comparison and data analysis.

This module provides advanced utilities for JSON comparison,
data normalization, and violation analysis.
"""

from typing import Any, Dict, List, Tuple, Optional, Set
import json
import re
from collections import defaultdict


class DataNormalizer:
    """Advanced data normalization for API responses."""

    @staticmethod
    def normalize_numeric_strings(value: Any) -> Any:
        """
        Convert numeric strings to numbers for comparison.
    
        Examples:
            "123" -> 123
            "0.05" -> 0.05
            "1.0" -> 1.0
        """
        if isinstance(value, str):
            try:
                if '.' not in value and 'e' not in value.lower():
                    return int(value)
            except (ValueError, TypeError):
                pass
            try:
                float_val = float(value)
                if float_val.is_integer():
                    return int(float_val)
                return float_val
            except (ValueError, TypeError):
                pass

        return value

    @staticmethod
    def normalize_hex_strings(value: Any) -> Any:
        """Normalize hex strings (case-insensitive comparison)."""
        if isinstance(value, str) and re.match(r'^[0-9a-fA-F]+$', value):
            return value.lower()
        return value
    
    @staticmethod
    def normalize_boolean_strings(value: Any) -> Any:
        """Convert boolean-like strings to actual booleans."""
        if isinstance(value, str):
            if value.lower() in ('true', 'yes', '1'):
                return True
            elif value.lower() in ('false', 'no', '0'):
                return False
        return value
    
    @staticmethod
    def normalize_null_values(value: Any) -> Any:
        """Normalize null/None/empty representations."""
        if value in (None, '', 'null', 'None'):
            return None
        return value
    
    @classmethod
    def normalize_all(cls, data: Any) -> Any:
        """Apply all normalization rules."""
        if isinstance(data, dict):
            return {k: cls.normalize_all(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.normalize_all(item) for item in data]
        else:
            # Apply normalizations in order
            data = cls.normalize_null_values(data)
            data = cls.normalize_boolean_strings(data)
            data = cls.normalize_numeric_strings(data)
            data = cls.normalize_hex_strings(data)
            return data


class ViolationAnalyzer:
    """Analyze and categorize API violations."""
    
    def __init__(self):
        self.violation_categories = defaultdict(list)
    
    def categorize_violation(self, violation_type: str, path: str, details: Dict) -> str:
        """
        Categorize a violation based on its type and characteristics.
        
        Returns:
            Category name (e.g., 'critical', 'formatting', 'minor')
        """
        # Critical violations - data integrity issues
        if violation_type == 'values_changed':
            if self._is_critical_field(path):
                return 'critical'
            elif self._is_numeric_precision_issue(details):
                return 'precision'
            else:
                return 'data_mismatch'
        
        # Missing fields
        elif violation_type == 'dictionary_item_removed':
            if self._is_required_field(path):
                return 'missing_required'
            else:
                return 'missing_optional'
        
        # Extra fields
        elif violation_type == 'dictionary_item_added':
            return 'extra_field'
        
        # Type mismatches
        elif violation_type == 'type_changes':
            return 'type_mismatch'
        
        return 'unknown'
    
    @staticmethod
    def _is_critical_field(path: str) -> bool:
        """Determine if a field is critical for data integrity."""
        critical_patterns = [
            'hash', 'id', 'address', 'amount', 'quantity',
            'epoch', 'slot', 'block', 'tx_index'
        ]
        return any(pattern in path.lower() for pattern in critical_patterns)
    
    @staticmethod
    def _is_required_field(path: str) -> bool:
        """Determine if a field is required by the API spec."""
        # This could be extended with actual schema validation
        required_patterns = ['hash', 'id', 'address']
        return any(pattern in path.lower() for pattern in required_patterns)
    
    @staticmethod
    def _is_numeric_precision_issue(details: Dict) -> bool:
        """Check if the issue is just numeric precision."""
        try:
            old_val = float(details.get('old_value', 0))
            new_val = float(details.get('new_value', 0))
            # If values are within 0.001% of each other, it's precision
            if old_val != 0:
                diff_percent = abs((new_val - old_val) / old_val)
                return diff_percent < 0.00001
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return False
    
    def analyze_violations(self, violations: List[Dict]) -> Dict[str, List[Dict]]:
        """Analyze and group violations by category."""
        categorized = defaultdict(list)
        
        for violation in violations:
            category = self.categorize_violation(
                violation.get('type', 'unknown'),
                violation.get('path', ''),
                violation.get('details', {})
            )
            categorized[category].append(violation)
        
        return dict(categorized)
    
    def get_severity_score(self, violations: List[Dict]) -> int:
        """
        Calculate severity score for violations.
        
        Returns:
            Score from 0 (no issues) to 100 (critical issues)
        """
        severity_weights = {
            'critical': 50,
            'missing_required': 30,
            'data_mismatch': 20,
            'type_mismatch': 15,
            'precision': 5,
            'missing_optional': 3,
            'extra_field': 2,
            'unknown': 10
        }
        
        categorized = self.analyze_violations(violations)
        score = 0
        
        for category, items in categorized.items():
            weight = severity_weights.get(category, 10)
            score += len(items) * weight
        
        return min(score, 100)  # Cap at 100


class ResponseComparator:
    """Advanced response comparison with detailed analysis."""
    
    def __init__(self, normalize: bool = True):
        self.normalize = normalize
        self.normalizer = DataNormalizer()
        self.analyzer = ViolationAnalyzer()
    
    def compare(
        self,
        response1: Dict,
        response2: Dict,
        ignore_fields: Optional[Set[str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare two responses with detailed analysis.
        
        Args:
            response1: First response (e.g., Blockfrost)
            response2: Second response (e.g., Dolos)
            ignore_fields: Set of field names to ignore in comparison
        
        Returns:
            Tuple of (is_identical, analysis_report)
        """
        if ignore_fields is None:
            ignore_fields = set()
        
        # Normalize if enabled
        if self.normalize:
            response1 = self.normalizer.normalize_all(response1)
            response2 = self.normalizer.normalize_all(response2)
        
        # Remove ignored fields
        response1 = self._remove_fields(response1, ignore_fields)
        response2 = self._remove_fields(response2, ignore_fields)
        
        # Perform comparison
        violations = self._deep_compare(response1, response2, path='root')
        
        # Analyze violations
        categorized = self.analyzer.analyze_violations(violations)
        severity = self.analyzer.get_severity_score(violations)
        
        is_identical = len(violations) == 0
        
        report = {
            'is_identical': is_identical,
            'violation_count': len(violations),
            'violations': violations,
            'categorized_violations': categorized,
            'severity_score': severity,
            'summary': self._generate_summary(categorized, severity)
        }
        
        return is_identical, report
    
    def _remove_fields(self, data: Any, fields: Set[str]) -> Any:
        """Remove specified fields from data structure."""
        if isinstance(data, dict):
            return {
                k: self._remove_fields(v, fields)
                for k, v in data.items()
                if k not in fields
            }
        elif isinstance(data, list):
            return [self._remove_fields(item, fields) for item in data]
        return data
    
    def _deep_compare(
        self,
        obj1: Any,
        obj2: Any,
        path: str = 'root'
    ) -> List[Dict]:
        """Recursively compare two objects."""
        violations = []
        
        # Type mismatch
        if type(obj1) != type(obj2):
            violations.append({
                'type': 'type_changes',
                'path': path,
                'details': {
                    'expected_type': type(obj1).__name__,
                    'actual_type': type(obj2).__name__,
                    'expected_value': obj1,
                    'actual_value': obj2
                }
            })
            return violations
        
        # Dictionary comparison
        if isinstance(obj1, dict):
            all_keys = set(obj1.keys()) | set(obj2.keys())
            
            for key in all_keys:
                new_path = f"{path}['{key}']"
                
                if key not in obj1:
                    violations.append({
                        'type': 'dictionary_item_added',
                        'path': new_path,
                        'details': {'value': obj2[key]}
                    })
                elif key not in obj2:
                    violations.append({
                        'type': 'dictionary_item_removed',
                        'path': new_path,
                        'details': {'value': obj1[key]}
                    })
                else:
                    violations.extend(
                        self._deep_compare(obj1[key], obj2[key], new_path)
                    )
        
        # List comparison
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                violations.append({
                    'type': 'list_length_changed',
                    'path': path,
                    'details': {
                        'expected_length': len(obj1),
                        'actual_length': len(obj2)
                    }
                })
            
            for i, (item1, item2) in enumerate(zip(obj1, obj2)):
                violations.extend(
                    self._deep_compare(item1, item2, f"{path}[{i}]")
                )
        
        # Value comparison
        else:
            if obj1 != obj2:
                violations.append({
                    'type': 'values_changed',
                    'path': path,
                    'details': {
                        'old_value': obj1,
                        'new_value': obj2
                    }
                })
        
        return violations
    
    def _generate_summary(
        self,
        categorized: Dict[str, List],
        severity: int
    ) -> str:
        """Generate human-readable summary of violations."""
        if not categorized:
            return "✓ No violations found - responses are identical"
        
        summary_parts = [f"Severity Score: {severity}/100"]
        
        if 'critical' in categorized:
            count = len(categorized['critical'])
            summary_parts.append(f"❌ {count} critical data integrity issue(s)")
        
        if 'missing_required' in categorized:
            count = len(categorized['missing_required'])
            summary_parts.append(f"⚠️  {count} required field(s) missing")
        
        if 'data_mismatch' in categorized:
            count = len(categorized['data_mismatch'])
            summary_parts.append(f"⚠️  {count} data value mismatch(es)")
        
        if 'type_mismatch' in categorized:
            count = len(categorized['type_mismatch'])
            summary_parts.append(f"⚠️  {count} data type mismatch(es)")
        
        if 'precision' in categorized:
            count = len(categorized['precision'])
            summary_parts.append(f"ℹ️  {count} numeric precision difference(s)")
        
        return "\n".join(summary_parts)


def format_violation_report(violations: List[Dict]) -> str:
    """Format violations into a readable report."""
    if not violations:
        return "✓ No violations found"
    
    lines = ["API Comparison Violations:", "=" * 80]
    
    for i, violation in enumerate(violations, 1):
        lines.append(f"\n{i}. {violation['type'].replace('_', ' ').title()}")
        lines.append(f"   Path: {violation['path']}")
        
        details = violation.get('details', {})
        for key, value in details.items():
            lines.append(f"   {key.replace('_', ' ').title()}: {value}")
    
    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def save_detailed_report(
    endpoint: str,
    report: Dict,
    output_file: str = "detailed_violations.json"
):
    """Save a detailed violation report to file."""
    full_report = {
        'endpoint': endpoint,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'analysis': report
    }
    
    with open(output_file, 'w') as f:
        json.dump(full_report, f, indent=2, default=str)
