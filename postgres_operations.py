import psycopg2

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
    def __init__(self, cursor: psycopg2.extensions.cursor):
        self.cursor = cursor


    def create_tables(self):
        for file_path in ddl_sql_file_paths.values():
            with open(file_path, 'r') as file:
                sql = file.read()
                self.cursor.execute(sql)


    def get_all_configs(self) -> list[tuple[str, str, str]]:
        with open(dql_sql_file_paths["get_all_configs"], 'r') as dql_file:
            sql = dql_file.read()
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result


    def insert_guild(self, guild_id: str, channel_id: str, role_id: str) -> str:
        with open(dml_sql_file_paths["insert_guild"], 'r') as dml_file:
            sql = dml_file.read().format(
                    guild_id=f"'{guild_id}'", 
                    channel_id=f"'{channel_id}'", 
                    role_id=f"'{role_id}'"
                )
            self.cursor.execute(sql)

            return sql


    def insert_historical(self, date: list[tuple[str]]) -> str:
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
            for entry in date:
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


    def read(self, guild_id: str) -> tuple[str, str]:
        with open(dql_sql_file_paths["read_config"], 'r') as dql_file:
            sql = dql_file.read().format(guild_id=f"'{guild_id}'")
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return result


from skillshot_scrap import get_hits_from_skillshot

if __name__ == "__main__":
    hits = get_hits_from_skillshot()
    print(hits)
    DBOperations(None).insert_historical(hits)