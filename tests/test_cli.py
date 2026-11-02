import contextlib
import importlib.util
import io
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

ARQUIVO = Path(__file__).resolve().parents[1] / "cli.py"

class Cli(unittest.TestCase):
    def setUp(self):
        self.cadastro = ModuleType("cadastro_biometria")
        self.cadastro.cadastrar_biometria = Mock(return_value=None)
        self.identificacao = ModuleType("identificacao_facial")
        self.identificacao.identificar_usuario = Mock(return_value=(7, .8))
        self.acesso = ModuleType("experimentos.teste_acesso_imagem")
        self.acesso.main = Mock(return_value={"resultado": "NEGADO"})
        self.bloqueados = {
            nome: None for nome in (
                "cv2", "mysql", "mysql.connector", "insightface", "insightface.app",
                "processamento_facial", "banco", "controle_acesso", "auditoria",
                "captura_webcam",
            )
        }
        isolamento = patch.dict(sys.modules, {
            **self.bloqueados,
            "cadastro_biometria": self.cadastro,
            "identificacao_facial": self.identificacao,
            "experimentos.teste_acesso_imagem": self.acesso,
        })
        isolamento.start()
        self.addCleanup(isolamento.stop)
        self.modulo = self.carregar()

    @staticmethod
    def carregar():
        spec = importlib.util.spec_from_file_location("cli_isolada", ARQUIVO)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def sem_chamadas(self):
        self.cadastro.cadastrar_biometria.assert_not_called()
        self.identificacao.identificar_usuario.assert_not_called()
        self.acesso.main.assert_not_called()

    def test_importacao_e_ajudas_sem_dependencias_ou_io(self):
        with patch.dict(sys.modules, {
            "cadastro_biometria": None, "identificacao_facial": None,
            "experimentos.teste_acesso_imagem": None,
        }), patch("builtins.open", side_effect=AssertionError("I/O proibido")), \
                contextlib.redirect_stdout(io.StringIO()) as saida:
            modulo = self.carregar()
            self.assertEqual(saida.getvalue(), "")
            for argumentos in (["--help"], ["cadastrar", "--help"],
                               ["identificar", "--help"], ["acesso", "--help"]):
                with self.subTest(argumentos=argumentos), self.assertRaises(SystemExit) as erro:
                    modulo.main(argumentos)
                self.assertEqual(erro.exception.code, 0)
        self.sem_chamadas()

    def test_cadastrar_delega_uma_vez(self):
        self.assertIsNone(self.modulo.main([
            "cadastrar", "--imagem", "pasta com espaço/ref.jpg", "--usuario", "7"]))
        self.cadastro.cadastrar_biometria.assert_called_once_with(
            id_usuario=7, caminho_imagem="pasta com espaço/ref.jpg")
        self.identificacao.identificar_usuario.assert_not_called()
        self.acesso.main.assert_not_called()

    def test_identificar_preserva_retorno_sem_autorizar(self):
        for resposta in ((7, .8), None):
            with self.subTest(resposta=resposta):
                self.identificacao.identificar_usuario.reset_mock()
                self.identificacao.identificar_usuario.return_value = resposta
                self.assertIs(self.modulo.main([
                    "identificar", "--imagem", "consulta.jpg"]), resposta)
                self.identificacao.identificar_usuario.assert_called_once_with(
                    caminho_imagem="consulta.jpg")
        self.cadastro.cadastrar_biometria.assert_not_called()
        self.acesso.main.assert_not_called()

    def test_acesso_delega_sem_reconhecer_antes_ou_validar_area(self):
        for area in ("2", "999999", "0", "-1"):
            with self.subTest(area=area):
                self.acesso.main.reset_mock()
                resposta = self.acesso.main.return_value
                self.assertIs(self.modulo.main([
                    "acesso", "--imagem", "consulta.jpg", "--area", area]), resposta)
                self.acesso.main.assert_called_once_with([
                    "--imagem", "consulta.jpg", "--area", area])
        self.cadastro.cadastrar_biometria.assert_not_called()
        self.identificacao.identificar_usuario.assert_not_called()

    def test_argumentos_invalidos_nao_iniciam_fluxo(self):
        casos = [[], ["inexistente"], ["cadastrar"], ["identificar"], ["acesso"],
                 ["cadastrar", "--imagem", "a.jpg", "--usuario", "abc"],
                 ["acesso", "--imagem", "a.jpg", "--area", "abc"],
                 ["identificar", "--imagem", "a.jpg", "--area", "2"],
                 ["cadastrar", "--imagem", "a.jpg"],
                 ["acesso", "--area", "2"]]
        with contextlib.redirect_stderr(io.StringIO()):
            for argumentos in casos:
                with self.subTest(argumentos=argumentos), self.assertRaises(SystemExit) as erro:
                    self.modulo.main(argumentos)
                self.assertEqual(erro.exception.code, 2)
        self.sem_chamadas()

    def test_excecoes_dos_comandos_sao_preservadas(self):
        casos = [
            (self.cadastro.cadastrar_biometria, ["cadastrar", "--imagem", "a.jpg", "--usuario", "7"]),
            (self.identificacao.identificar_usuario, ["identificar", "--imagem", "a.jpg"]),
            (self.acesso.main, ["acesso", "--imagem", "a.jpg", "--area", "2"]),
        ]
        for funcao, argumentos in casos:
            with self.subTest(comando=argumentos[0]):
                erro = ValueError("Falha simulada")
                funcao.side_effect = erro
                with self.assertRaises(ValueError) as contexto:
                    self.modulo.main(argumentos)
                self.assertIs(contexto.exception, erro)
                funcao.side_effect = None

if __name__ == "__main__":
    unittest.main()
