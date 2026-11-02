import contextlib
import importlib.util
import io
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

ARQUIVO = Path(__file__).resolve().parents[1] / "experimentos" / "teste_acesso_imagem.py"

class ErroDeteccaoSimulado(ValueError):
    pass

class AcessoImagem(unittest.TestCase):
    def setUp(self):
        self.controle = ModuleType("controle_acesso")
        self.controle.solicitar_acesso = Mock()
        self.processamento = ModuleType("processamento_facial")
        self.processamento.ErroDeteccaoFacial = ErroDeteccaoSimulado
        self.auditoria = ModuleType("auditoria")
        self.auditoria.registrar_falha_biometrica = Mock()
        substituicoes = {
            "controle_acesso": self.controle,
            "processamento_facial": self.processamento,
            "auditoria": self.auditoria,
            "cv2": None, "mysql": None, "mysql.connector": None,
            "insightface": None, "insightface.app": None,
            "banco": None, "identificacao_facial": None,
        }
        isolamento = patch.dict(sys.modules, substituicoes)
        isolamento.start()
        self.addCleanup(isolamento.stop)
        self.modulo = self.carregar()
        self.saida = io.StringIO()
        redirecionar = contextlib.redirect_stdout(self.saida)
        redirecionar.__enter__()
        self.addCleanup(redirecionar.__exit__, None, None, None)

    @staticmethod
    def carregar():
        spec = importlib.util.spec_from_file_location("auxiliar_acesso_imagem", ARQUIVO)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def executar(self, area="2", imagem="pasta com espaço/imagem.jpg"):
        return self.modulo.main(["--imagem", imagem, "--area", area])

    def test_importacao_e_help_sem_dependencias_ou_io(self):
        with patch.dict(sys.modules, {
            "controle_acesso": None, "processamento_facial": None, "auditoria": None,
        }), patch("builtins.open", side_effect=AssertionError("I/O proibido")):
            modulo = self.carregar()
            with self.assertRaises(SystemExit) as contexto:
                modulo.main(["--help"])
        self.assertEqual(contexto.exception.code, 0)
        self.controle.solicitar_acesso.assert_not_called()
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_delega_uma_vez_e_preserva_resposta_e_saida_existente(self):
        resposta = dict(usuario="Teste", area="Laboratório", resultado="PERMITIDO", motivo="Nível suficiente")

        def solicitar(**kwargs):
            print("Usuário: Teste\nSimilaridade: 0.8765\nÁrea: Laboratório\nResultado: PERMITIDO\nMotivo: Nível suficiente")
            return resposta

        self.controle.solicitar_acesso.side_effect = solicitar
        self.assertIs(self.executar(), resposta)
        self.controle.solicitar_acesso.assert_called_once_with(
            id_area=2, caminho_imagem="pasta com espaço/imagem.jpg")
        for texto in ("ID da área solicitada: 2", "Similaridade: 0.8765", "Usuário: Teste",
                      "Área: Laboratório", "Resultado: PERMITIDO", "Motivo: Nível suficiente"):
            self.assertIn(texto, self.saida.getvalue())
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_negativa_da_procedure_preservada_sem_auditoria_adicional(self):
        resposta = {"resultado": "NEGADO", "motivo": "Nível insuficiente"}
        self.controle.solicitar_acesso.return_value = resposta
        self.assertIs(self.executar(), resposta)
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_desconhecido_nao_audita_novamente(self):
        self.controle.solicitar_acesso.return_value = None
        self.assertIsNone(self.executar())
        self.controle.solicitar_acesso.assert_called_once()
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_ausencia_ou_multiplos_rostos_audita_uma_vez(self):
        for motivo in ("Nenhuma face detectada", "Múltiplas faces detectadas"):
            with self.subTest(motivo=motivo):
                self.auditoria.registrar_falha_biometrica.reset_mock()
                self.controle.solicitar_acesso.side_effect = ErroDeteccaoSimulado(motivo)
                self.assertIsNone(self.executar())
                self.auditoria.registrar_falha_biometrica.assert_called_once_with(
                    id_area_solicitada=2, motivo=motivo)
                self.assertIn(f"Motivo: {motivo}", self.saida.getvalue())

    def test_imagem_inexistente_ou_ilegivel_nao_audita(self):
        self.controle.solicitar_acesso.side_effect = ValueError("Não foi possível carregar: ausente.jpg")
        self.assertIsNone(self.executar(imagem="ausente.jpg"))
        self.assertIn("Não foi possível concluir", self.saida.getvalue())
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_area_encaminhada_sem_validacao_de_existencia(self):
        for area in ("999999", "0", "-1"):
            with self.subTest(area=area):
                self.controle.solicitar_acesso.reset_mock()
                self.executar(area=area)
                self.controle.solicitar_acesso.assert_called_once_with(
                    id_area=int(area), caminho_imagem="pasta com espaço/imagem.jpg")
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_erro_operacional_nao_vira_negativa_biometrica(self):
        self.controle.solicitar_acesso.side_effect = RuntimeError("Falha simulada")
        self.assertIsNone(self.executar())
        self.assertIn("Ocorreu um erro inesperado", self.saida.getvalue())
        self.assertNotIn("ACESSO NEGADO", self.saida.getvalue())
        self.auditoria.registrar_falha_biometrica.assert_not_called()

    def test_falha_auditoria_nao_e_repetida(self):
        self.controle.solicitar_acesso.side_effect = ErroDeteccaoSimulado("Nenhuma face detectada")
        self.auditoria.registrar_falha_biometrica.side_effect = RuntimeError("Auditoria indisponível")
        self.assertIsNone(self.executar())
        self.auditoria.registrar_falha_biometrica.assert_called_once()
        self.assertIn("Auditoria indisponível", self.saida.getvalue())
        self.assertNotIn("ACESSO NEGADO", self.saida.getvalue())

    def test_argumentos_invalidos_nao_iniciam_fluxo(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for argumentos in ([], ["--imagem", "teste.jpg", "--area", "abc"]):
                with self.subTest(argumentos=argumentos), self.assertRaises(SystemExit) as contexto:
                    self.modulo.main(argumentos)
                self.assertEqual(contexto.exception.code, 2)
        self.controle.solicitar_acesso.assert_not_called()
        self.auditoria.registrar_falha_biometrica.assert_not_called()

if __name__ == "__main__":
    unittest.main()
