from contextlib import closing
import json
import csv
import mysql.connector

MAX_FETCH_SIZE = 10000


class MysqlDumpQueryToTSV(object):

    def __init__(self, host, username, password, database, destination_filename):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.destination_filename  = destination_filename

    def execute(self, query):
        with self._connect() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)

                with open(self.destination_filename, 'w') as output_file:
                    self._write_results_to_tsv(cursor, output_file)
            finally:
                cursor.close()

    def _connect(self):
        connection = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=self.database,
        )

        return closing(connection)

    def _write_results_to_tsv(self, cursor, output_file):
        """
        Writes each row to a TSV file.
        Fields are separated by tabs, no quote character.
        Output would be encoded as utf-8.
        All embeded tabs(\t), newlines(\n), and carriage returns(\r) are escaped.
        """

        writer = csv.writer(output_file, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar='', lineterminator='\n')

        writer.writerow(cursor.column_names)

        while True:
            rows = cursor.fetchmany(size=MAX_FETCH_SIZE)
            if not rows:
                break

            for row in rows:
                converted_row = [self._normalize_value(v) for v in row]
                writer.writerow(converted_row)

            # Custom Proversity fix to avoid infinite loop at last row of the query results.
            # If less than MAX_FETCH_SIZE rows were fetched in this loop then is safe to
            # assume there won't be anymore results and we can exit the cycle.
            if len(rows) < MAX_FETCH_SIZE:
                break

    def _normalize_value(self, value):
        if value is None: value='NULL'
        return unicode(value).encode('utf-8').replace('\\', '\\\\').replace('\r', '\\r').replace('\t','\\t').replace('\n', '\\n')
