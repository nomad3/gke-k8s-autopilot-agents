"""
AI-Assisted Schema Mapping Service

Uses LLM to intelligently map source fields to target schema
Learns from previous mappings and user corrections
"""

from typing import Any, Dict, List, Optional

from ..utils.logger import logger


class SchemaMapper:
    """
    AI-assisted schema mapping service

    Features:
    - Automatic field mapping using similarity
    - LLM-powered intelligent suggestions
    - Learning from historical mappings
    - User correction feedback loop
    """

    def __init__(self):
        self._mapping_cache: Dict[str, Dict[str, str]] = {}
        self._llm_enabled = False  # TODO: Enable when LLM configured

    async def map_fields(
        self,
        source_system: str,
        entity_type: str,
        source_fields: List[str],
        target_schema: Dict[str, Any],
        sample_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Map source fields to target schema

        Args:
            source_system: Source system name (e.g., 'netsuite', 'adp')
            entity_type: Entity type (e.g., 'customer', 'employee')
            source_fields: List of source field names
            target_schema: Target schema definition
            sample_data: Optional sample record for context

        Returns:
            Dict mapping source_field -> target_field
        """
        cache_key = f"{source_system}:{entity_type}"

        # Check cache first
        if cache_key in self._mapping_cache:
            logger.info(f"Using cached mapping for {cache_key}")
            return self._mapping_cache[cache_key]

        # Generate mapping
        if self._llm_enabled and sample_data:
            mapping = await self._llm_assisted_mapping(
                source_system,
                entity_type,
                source_fields,
                target_schema,
                sample_data
            )
        else:
            mapping = self._rule_based_mapping(
                source_system,
                entity_type,
                source_fields,
                target_schema
            )

        # Cache the mapping
        self._mapping_cache[cache_key] = mapping

        logger.info(f"Generated mapping for {cache_key}: {len(mapping)} fields mapped")
        return mapping

    def _rule_based_mapping(
        self,
        source_system: str,
        entity_type: str,
        source_fields: List[str],
        target_schema: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Rule-based field mapping using naming conventions

        Args:
            source_system: Source system
            entity_type: Entity type
            source_fields: Source fields
            target_schema: Target schema

        Returns:
            Field mapping dictionary
        """
        mapping = {}
        target_fields = list(target_schema.keys())

        # Exact match first
        for source_field in source_fields:
            if source_field in target_fields:
                mapping[source_field] = source_field

        # Common transformations
        common_mappings = {
            # NetSuite specific
            "tranId": "transaction_id",
            "tranDate": "transaction_date",
            "internalId": "internal_id",
            "entityId": "entity_id",
            "companyName": "company_name",
            "familyName1": "last_name",
            "givenName": "first_name",

            # ADP specific
            "workerID": "employee_id",
            "associateOID": "internal_id",
            "emailUri": "email",

            # Common fields
            "id": "id",
            "email": "email",
            "phone": "phone",
            "status": "status",
            "createdDate": "created_at",
            "lastModifiedDate": "updated_at",
        }

        # Apply common mappings
        for source_field in source_fields:
            if source_field not in mapping and source_field in common_mappings:
                target_field = common_mappings[source_field]
                if target_field in target_fields:
                    mapping[source_field] = target_field

        # Fuzzy match for remaining fields
        for source_field in source_fields:
            if source_field not in mapping:
                best_match = self._find_best_match(source_field, target_fields)
                if best_match:
                    mapping[source_field] = best_match

        return mapping

    def _find_best_match(
        self,
        source_field: str,
        target_fields: List[str],
        threshold: float = 0.7
    ) -> Optional[str]:
        """
        Find best matching target field using similarity

        Args:
            source_field: Source field name
            target_fields: List of target field names
            threshold: Minimum similarity score

        Returns:
            Best matching target field or None
        """
        source_lower = source_field.lower()
        best_score = 0.0
        best_match = None

        for target_field in target_fields:
            target_lower = target_field.lower()

            # Simple substring matching
            if source_lower in target_lower or target_lower in source_lower:
                score = min(len(source_lower), len(target_lower)) / max(len(source_lower), len(target_lower))

                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = target_field

        return best_match

    async def _llm_assisted_mapping(
        self,
        source_system: str,
        entity_type: str,
        source_fields: List[str],
        target_schema: Dict[str, Any],
        sample_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Use LLM to intelligently map fields

        Args:
            source_system: Source system
            entity_type: Entity type
            source_fields: Source fields
            target_schema: Target schema
            sample_data: Sample record for context

        Returns:
            LLM-generated field mapping
        """
        # TODO: Implement LLM-powered mapping
        # This would use OpenAI/Anthropic API to analyze:
        # 1. Field names
        # 2. Sample data values
        # 3. Schema descriptions
        # 4. Historical mappings
        # And generate intelligent mappings

        logger.info("LLM-assisted mapping not yet implemented, falling back to rules")
        return self._rule_based_mapping(source_system, entity_type, source_fields, target_schema)

    async def save_mapping_correction(
        self,
        source_system: str,
        entity_type: str,
        source_field: str,
        target_field: str
    ):
        """
        Save user correction to mapping

        This feedback loop improves future mappings

        Args:
            source_system: Source system
            entity_type: Entity type
            source_field: Source field name
            target_field: Corrected target field name
        """
        cache_key = f"{source_system}:{entity_type}"

        if cache_key not in self._mapping_cache:
            self._mapping_cache[cache_key] = {}

        self._mapping_cache[cache_key][source_field] = target_field

        # TODO: Save to database for persistence and ML training
        logger.info(f"Saved mapping correction: {source_field} -> {target_field}")


# Singleton instance
_schema_mapper: Optional[SchemaMapper] = None


def get_schema_mapper() -> SchemaMapper:
    """Get singleton schema mapper"""
    global _schema_mapper
    if _schema_mapper is None:
        _schema_mapper = SchemaMapper()
    return _schema_mapper
