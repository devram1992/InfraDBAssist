from __future__ import annotations

import json
from datetime import datetime

from backend.app.database.connection import get_connection


class CapacityRepository:
    """
    Repository for storing and retrieving capacity measurements.

    This repository is source-agnostic. Measurements can come from
    Oracle, Grafana, Linux, Kubernetes, PostgreSQL, or any future
    monitoring integration.
    """

    def record_measurement(
        self,
        observed_at: datetime,
        environment: str,
        source: str,
        target: str,
        resource: str,
        metric: str,
        value: float,
        unit: str,
        metadata: dict | None = None,
    ) -> int:
        """
        Store a single capacity measurement.

        Returns:
            Newly created measurement ID.
        """

        if not environment or not environment.strip():
            raise ValueError(
                "Environment cannot be empty."
            )

        if not source or not source.strip():
            raise ValueError(
                "Source cannot be empty."
            )

        if not target or not target.strip():
            raise ValueError(
                "Target cannot be empty."
            )

        if not metric or not metric.strip():
            raise ValueError(
                "Metric cannot be empty."
            )

        if not unit or not unit.strip():
            raise ValueError(
                "Unit cannot be empty."
            )

        if not isinstance(value, (int, float)):
            raise ValueError(
                "Measurement value must be numeric."
            )

        metadata_json = json.dumps(
            metadata or {}
        )

        query = """
            INSERT INTO capacity_measurements (
                observed_at,
                environment,
                source,
                target,
                resource,
                metric,
                value,
                unit,
                metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (
                environment,
                source,
                target,
                resource,
                metric,
                unit,
                observed_at
            )
            DO UPDATE SET
                value = EXCLUDED.value,
                metadata = EXCLUDED.metadata
            RETURNING id;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        observed_at,
                        environment,
                        source,
                        target,
                        resource,
                        metric,
                        value,
                        unit,
                        metadata_json,
                    ),
                )

                measurement_id = (
                    cursor.fetchone()[0]
                )

                conn.commit()

                return measurement_id

    def get_measurements(
        self,
        environment: str,
        source: str,
        target: str,
        resource: str,
        metric: str,
        unit: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Retrieve historical measurements for forecasting.
        """

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        query = """
            SELECT
                id,
                observed_at,
                environment,
                source,
                target,
                resource,
                metric,
                value,
                unit,
                metadata,
                created_at
            FROM capacity_measurements
            WHERE environment = %s
              AND source = %s
              AND target = %s
              AND resource = %s
              AND metric = %s
        """

        parameters: list = [
            environment,
            source,
            target,
            resource,
            metric,
        ]

        if unit is not None:
            query += """
                AND unit = %s
            """

            parameters.append(unit)

        if start_time is not None:
            query += """
                AND observed_at >= %s
            """

            parameters.append(start_time)

        if end_time is not None:
            query += """
                AND observed_at <= %s
            """

            parameters.append(end_time)

        query += """
            ORDER BY observed_at ASC
            LIMIT %s
        """

        parameters.append(limit)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    parameters,
                )

                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "observed_at": row[1],
                        "environment": row[2],
                        "source": row[3],
                        "target": row[4],
                        "resource": row[5],
                        "metric": row[6],
                        "value": float(row[7]),
                        "unit": row[8],
                        "metadata": row[9],
                        "created_at": row[10],
                    }
                    for row in rows
                ]

    def get_latest_measurement(
        self,
        environment: str,
        source: str,
        target: str,
        resource: str,
        metric: str,
        unit: str | None = None,
    ) -> dict | None:
        """
        Retrieve the most recent measurement for a metric.
        """

        query = """
            SELECT
                id,
                observed_at,
                environment,
                source,
                target,
                resource,
                metric,
                value,
                unit,
                metadata,
                created_at
            FROM capacity_measurements
            WHERE environment = %s
              AND source = %s
              AND target = %s
              AND resource = %s
              AND metric = %s
        """

        parameters: list = [
            environment,
            source,
            target,
            resource,
            metric,
        ]

        if unit is not None:
            query += """
                AND unit = %s
            """

            parameters.append(unit)

        query += """
            ORDER BY observed_at DESC
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    parameters,
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                return {
                    "id": row[0],
                    "observed_at": row[1],
                    "environment": row[2],
                    "source": row[3],
                    "target": row[4],
                    "resource": row[5],
                    "metric": row[6],
                    "value": float(row[7]),
                    "unit": row[8],
                    "metadata": row[9],
                    "created_at": row[10],
                }

    def count_measurements(
        self,
        environment: str,
        source: str,
        target: str,
        resource: str,
        metric: str,
        unit: str | None = None,
    ) -> int:
        """
        Return the number of stored measurements for a metric.
        """

        query = """
            SELECT COUNT(*)
            FROM capacity_measurements
            WHERE environment = %s
              AND source = %s
              AND target = %s
              AND resource = %s
              AND metric = %s
        """

        parameters: list = [
            environment,
            source,
            target,
            resource,
            metric,
        ]

        if unit is not None:
            query += """
                AND unit = %s
            """

            parameters.append(unit)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    parameters,
                )

                return int(
                    cursor.fetchone()[0]
                )
