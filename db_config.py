import psycopg2

try:
    connect_str = "dbname='bsocial' user='mirko' host='localhost' password='sifra123'"
    conn = psycopg2.connect(connect_str)
    cursor = conn.cursor()
    cursor.execute("select * from information_schema.tables where table_name=%s", ('users',))
    table_check = cursor.fetchall()
    if not table_check:
        cursor.execute("""CREATE TABLE users (
            name varchar,
            surname varchar,
            username varchar,
            email varchar,
            password varchar,
            PRIMARY KEY (username));""")
        conn.commit()
    cursor.execute("select * from information_schema.tables where table_name=%s", ('posts',))
    table_check = cursor.fetchall()
    if not table_check:
        cursor.execute("""CREATE TABLE posts (
            user_username varchar REFERENCES users(username),
            post varchar,
            post_privacy varchar,
            datetime timestamp,
            id_post serial,
            PRIMARY KEY(id_post));""")
        conn.commit()
    cursor.execute("select * from information_schema.tables where table_name=%s", ('followers',))
    table_check = cursor.fetchall()
    if not table_check:
        cursor.execute("""CREATE TABLE followers (
            username varchar REFERENCES users(username),
            follows varchar REFERENCES users(username),
            id_follow serial,
            PRIMARY KEY(id_follow));""")
        conn.commit()
    cursor.execute("select * from information_schema.tables where table_name=%s", ('comments',))
    table_check = cursor.fetchall()
    if not table_check:
        cursor.execute("""CREATE TABLE comments (
            username varchar REFERENCES users(username),
            post_id integer REFERENCES posts(id_post),
            comment varchar,
            datetime timestamp,
            id_comment serial,
            PRIMARY KEY(id_comment));""")
        conn.commit()
except Exception as e:
    print("Uh oh, can't connect. Invalid dbname, user or password?")
    print(e)