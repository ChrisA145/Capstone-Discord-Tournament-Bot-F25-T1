import peewee

#create a sql db connection
tournament_dbc = peewee.SqliteDatabase("ksu_tournament.db")