import psycopg2
import datetime

ddl_sql_file_paths = {
    "create_configs_table": "sql/ddl/configs.sql",
    "create_historical_table": "sql/ddl/historical_data.sql",
}

dml_sql_file_paths = {
    "insert_guild": "sql/dml/insert_guild.sql",
    "insert_historical": "sql/dml/insert_historical.sql",
    "update_channel": "sql/dml/update_channel.sql",
    "update_role": "sql/dml/update_role.sql",
}

dql_sql_file_paths = {
    "read_config": "sql/dql/get_config.sql",
    "get_all_configs": "sql/dql/get_all_configs.sql",
}


class DBOperations:
    """
    Postgres database operations for sql files

    :param psycopg2.extensions.cursor cursor: psycopg2 cursor object
    """
    def __init__(self, cursor: psycopg2.extensions.cursor):
        self.cursor = cursor


    def create_tables(self):
        """
        Initialize database tables from DDL sql files
        """
        for file_path in ddl_sql_file_paths.values():
            with open(file_path, 'r') as file:
                sql = file.read()
                self.cursor.execute(sql)


    def get_all_configs(self) -> list[tuple[str, str, str]]:
        """
        Fetch all guild configurations from database

        :return: list of tuples with the following structure:
                    (guild_id, channel_id, role_id)
        :rtype: list[tuple[str, str, str]]
        """
        with open(dql_sql_file_paths["get_all_configs"], 'r') as dql_file:
            sql = dql_file.read()
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result


    def insert_guild(self, guild_id: str, channel_id: str, role_id: str) -> str:
        """
        Insert new guild configuration into database

        :param str guild_id: discord guild ID
        :param str channel_id: discord channel ID
        :param str role_id: discord role ID
        :return: executed sql statement
        :rtype: str
        """
        with open(dml_sql_file_paths["insert_guild"], 'r') as dml_file:
            sql = dml_file.read().format(
                    guild_id=f"'{guild_id}'", 
                    channel_id=f"'{channel_id}'", 
                    role_id=f"'{role_id}'"
                )
            self.cursor.execute(sql)

            return sql


    def insert_historical(self, entries: list[tuple[str, str, datetime.datetime, str, str]]) -> str:
        """
        Insert new historical job offers into database
        Generates MD5 hash based on offer name, company and date as primary key

        :param list[tuple[str]] date: list of tuples with the following structure:
                    (role, discord_message_tpl, dt_date, company, location)
        :return: executed sql statement
        :rtype: str
        """

        value_template = """(
    MD5({offer_name} || {company} || {date_added})
    , CASE 
        WHEN LOWER({offer_name}) LIKE '%intern%' THEN 'intern'
        WHEN LOWER({offer_name}) LIKE '%staż%' THEN 'intern'
        WHEN LOWER({offer_name}) LIKE '%junior%' THEN 'junior'
        WHEN LOWER({offer_name}) LIKE '%jr%' THEN 'junior'
        WHEN LOWER({offer_name}) LIKE '%mid%' THEN 'mid'
        WHEN LOWER({offer_name}) LIKE '%senior%' THEN 'senior'
        WHEN LOWER({offer_name}) LIKE '%lead%' THEN 'lead'
        WHEN LOWER({offer_name}) LIKE '%principal%' THEN 'lead'
        ELSE 'mid'
    END
    , {date_added}
    , {offer_name}
    , {city}
    , {company}
)
,
"""
        with open(dml_sql_file_paths["insert_historical"], 'r') as dml_file:
            sql = dml_file.read()
            values = ""
            for entry in entries:
                values += value_template.format(
                    offer_name=f"'{entry[0]}'",
                    date_added=f"'{entry[2].strftime('%Y-%m-%d')}'",
                    company=f"'{entry[3]}'",
                    city=f"'{entry[4]}'"
                )
            sql = sql.replace("{values}", values[:-3])

        self.cursor.execute(sql)

        return sql


    def update(self, guild_id: str, channel_id: str = None, role_id: str = None) -> str:
        """
        Update guild configuration in database

        :param str guild_id: discord guild ID
        
        :param channel_id: discord channel ID
        :type channel_id: str | None
        :param role_id: discord role ID
        :type role_id: str | None

        :return: executed sql statement
        :rtype: str
        """
        if channel_id is not None:
            with open(dml_sql_file_paths["update_channel"], 'r') as dml_file:
                sql = dml_file.read().format(guild_id=f"'{guild_id}'", channel_id=f"'{channel_id}'")
                self.cursor.execute(sql)

                return sql
        
        if role_id is not None:
            with open(dml_sql_file_paths["update_role"], 'r') as dml_file:
                sql = dml_file.read().format(guild_id=f"'{guild_id}'", role_id=f"'{role_id}'")
                self.cursor.execute(sql)

                return sql


    def read(self, guild_id: str) -> tuple[str]:
        """
        Fetch guild configuration from database
        :param str guild_id: discord guild ID
        :return: tuple with the following structure:
                    (guild_id)
        :rtype: tuple[str]
        """
        with open(dql_sql_file_paths["read_config"], 'r') as dql_file:
            sql = dql_file.read().format(guild_id=f"'{guild_id}'")
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result
    

    def backfill(self, date_from: datetime.datetime) -> str:
        """
        Backfill historical job offers from skillshot.pl from given date

        :param datetime.datetime date_from: earliest date to backfill job offers from
        :return: executed sql statement
        :rtype: str
        """
        from skillshot_scrap import get_hits_from_skillshot

        hits = get_hits_from_skillshot(pages=5, date_to_compare=date_from)
        return self.insert_historical(hits)
