import os
import sqlite3
import asyncio
import asyncpg
from datetime import datetime, date


SQLITE_DB = "mplads.db"

TABLES = [
    "users",
    "mps",
    "districts",
    "contractors",
    "projects",
    "milestones",
    "evidence",
    "fund_disbursements",
    "anomaly_logs",
    "audit_logs",
    "notifications",
]


DATE_COLUMNS = {
    "registered_date",
    "start_date",
    "target_completion_date",
    "actual_completion_date",
    "planned_date",
    "actual_date",
    "disbursement_date",

    "planned_start_date",
    "planned_end_date",
    "actual_start_date",
    "actual_end_date",

    "detected_at",
    "uploaded_at",
    "created_at",
    "timestamp",
}

BOOLEAN_COLUMNS = {
    "blacklisted_status",
    "geo_anomaly_flag",
    "is_flagged",
    "is_duplicate_flag",
    "is_read",
}


DATE_ONLY_COLUMNS = {
    "registered_date",
    "start_date",
    "target_completion_date",
    "actual_completion_date",
    "planned_date",
    "actual_date",
    "disbursement_date",

    "planned_start_date",
    "planned_end_date",
    "actual_start_date",
    "actual_end_date",
}

DATETIME_COLUMNS = {
    "detected_at",
    "uploaded_at",
    "created_at",
    "timestamp",
}


def convert_value(value, column):

    if value is None:
        return None

    # Boolean conversion
    if column in BOOLEAN_COLUMNS:

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return value != 0

        if isinstance(value, str):

            value = value.strip().lower()

            if value in {
                "1",
                "true",
                "t",
                "yes"
            }:
                return True

            if value in {
                "0",
                "false",
                "f",
                "no"
            }:
                return False

        return bool(value)

    # Date / datetime conversion
    if column in DATE_COLUMNS:

        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return value

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

            # Date only
            if column in DATE_ONLY_COLUMNS:

                try:
                    return date.fromisoformat(
                        value[:10]
                    )
                except ValueError:
                    pass

            # Datetime
            if column in DATETIME_COLUMNS:

                formats = [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                ]

                for fmt in formats:

                    try:
                        return datetime.strptime(
                            value,
                            fmt
                        )

                    except ValueError:
                        continue

            # Generic fallback
            try:
                return date.fromisoformat(
                    value[:10]
                )

            except ValueError:
                pass

    return value


def read_sqlite():

    conn = sqlite3.connect(
        SQLITE_DB
    )

    conn.row_factory = sqlite3.Row

    data = {}

    for table in TABLES:

        rows = conn.execute(
            f'SELECT * FROM "{table}"'
        ).fetchall()

        converted_rows = []

        for row in rows:

            converted = {}

            for column in row.keys():

                converted[column] = convert_value(
                    row[column],
                    column
                )

            converted_rows.append(
                converted
            )

        data[table] = converted_rows

        print(
            f"{table}: "
            f"{len(converted_rows)}"
        )

    conn.close()

    return data


async def main():

    database_url = os.getenv(
        "DATABASE_URL"
    )

    if not database_url:

        raise RuntimeError(
            "DATABASE_URL is not set."
        )

    if database_url.startswith(
        "postgresql+asyncpg://"
    ):

        database_url = database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1
        )

    elif database_url.startswith(
        "postgres://"
    ):

        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    print(
        "\nReading SQLite database..."
    )

    data = read_sqlite()

    print(
        "\nConnecting to Supabase..."
    )

    conn = await asyncpg.connect(
        database_url
    )

    try:

        print(
            "\nClearing Supabase tables..."
        )

        for table in reversed(TABLES):

            await conn.execute(
                f'''
                TRUNCATE TABLE "{table}"
                RESTART IDENTITY CASCADE
                '''
            )

        print(
            "Supabase tables cleared."
        )

        print(
            "\nMigrating data...\n"
        )

        for table in TABLES:

            rows = data[table]

            if not rows:
                continue

            columns = list(
                rows[0].keys()
            )

            column_sql = ", ".join(
                f'"{column}"'
                for column in columns
            )

            placeholders = ", ".join(
                f"${i + 1}"
                for i in range(len(columns))
            )

            query = f'''
                INSERT INTO "{table}"
                ({column_sql})
                VALUES ({placeholders})
            '''

            values = []

            for row in rows:

                values.append(
                    tuple(
                        row[column]
                        for column in columns
                    )
                )

            await conn.executemany(
                query,
                values
            )

            print(
                f"✓ {table}: "
                f"{len(rows)} records"
            )

        print(
            "\nVerifying migration...\n"
        )

        all_correct = True

        for table in TABLES:

            count = await conn.fetchval(
                f'''
                SELECT COUNT(*)
                FROM "{table}"
                '''
            )

            expected = len(
                data[table]
            )

            if count == expected:

                print(
                    f"✓ {table}: "
                    f"{count} / {expected}"
                )

            else:

                all_correct = False

                print(
                    f"✗ {table}: "
                    f"{count} / {expected}"
                )

        print()

        if all_correct:

            print(
                "================================"
            )

            print(
                "MIGRATION COMPLETED SUCCESSFULLY"
            )

            print(
                "================================"
            )

        else:

            print(
                "Migration completed "
                "with count mismatches."
            )

    finally:

        await conn.close()


if __name__ == "__main__":

    asyncio.run(main())