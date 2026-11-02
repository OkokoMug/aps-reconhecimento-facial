import os
import mysql.connector

def conectar_banco():

    variaveis = {
        "host": "APS_DB_HOST",
        "user": "APS_DB_USER",
        "password": "APS_DB_PASSWORD",
        "database": "APS_DB_NAME",
    }

    configuracao = {campo: os.environ.get(nome) for campo, nome in variaveis.items()}
    ausentes = [nome for campo, nome in variaveis.items() if not configuracao[campo]]

    if ausentes:
        raise ValueError("Configura??o MySQL ausente: " + ", ".join(ausentes))
    return mysql.connector.connect(**configuracao)
