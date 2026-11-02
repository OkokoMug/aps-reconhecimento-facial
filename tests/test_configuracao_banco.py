import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

class ConfiguracaoBanco(unittest.TestCase):
    def setUp(self):
        connector = ModuleType("mysql.connector")
        connector.connect = Mock()
        mysql = ModuleType("mysql")
        mysql.connector = connector
        self.conectar = connector.connect
        with patch.dict(sys.modules, {"mysql": mysql, "mysql.connector": connector}):
            spec = importlib.util.spec_from_file_location(
                "banco_isolado", Path(__file__).resolve().parents[1] / "banco.py")
            self.modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modulo)
        self.ambiente = {
            "APS_DB_HOST": "host_ficticio", "APS_DB_USER": "usuario_ficticio",
            "APS_DB_PASSWORD": "segredo_sintetico", "APS_DB_NAME": "banco_ficticio",
        }

    def test_importacao_nao_conecta(self):
        self.conectar.assert_not_called()

    def test_encaminha_configuracao_e_preserva_retorno(self):
        with patch.dict(os.environ, self.ambiente, clear=True):
            self.assertIs(self.modulo.conectar_banco(), self.conectar.return_value)
        self.conectar.assert_called_once_with(
            host="host_ficticio", user="usuario_ficticio",
            password="segredo_sintetico", database="banco_ficticio")

    def test_ausente_ou_vazia_nao_conecta_nem_expoe_valores(self):
        for nome in self.ambiente:
            for valor in (None, ""):
                with self.subTest(nome=nome, vazio=valor == ""):
                    ambiente = dict(self.ambiente)
                    if valor is None:
                        del ambiente[nome]
                    else:
                        ambiente[nome] = valor
                    with patch.dict(os.environ, ambiente, clear=True):
                        with self.assertRaises(ValueError) as erro:
                            self.modulo.conectar_banco()
                    self.assertIn(nome, str(erro.exception))
                    for sensivel in self.ambiente.values():
                        self.assertNotIn(sensivel, str(erro.exception))
        self.conectar.assert_not_called()

    def test_le_ambiente_a_cada_chamada(self):
        with patch.dict(os.environ, self.ambiente, clear=True):
            self.modulo.conectar_banco()
            os.environ["APS_DB_NAME"] = "outro_banco_ficticio"
            self.modulo.conectar_banco()
        self.assertEqual(self.conectar.call_args.kwargs["database"], "outro_banco_ficticio")

    def test_erro_connector_preserva_excecao(self):
        erro = RuntimeError("Falha simulada")
        self.conectar.side_effect = erro
        with patch.dict(os.environ, self.ambiente, clear=True):
            with self.assertRaises(RuntimeError) as contexto:
                self.modulo.conectar_banco()
        self.assertIs(contexto.exception, erro)
