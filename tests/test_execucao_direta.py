import contextlib
import io
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
EXPERIMENTO = RAIZ / "experimentos" / "teste_banco_embedding.py"


class ExecucaoDireta(unittest.TestCase):
    def test_modulos_centrais_nao_executam_operacoes(self):
        membros = {
            "banco": ("conectar_banco",),
            "repositorio_biometrias": ("buscar_usuario", "inserir_biometria"),
            "processamento_facial": ("app", "ErroDeteccaoFacial", "extrair_embedding", "extrair_embedding_frame"),
            "identificacao_facial": ("identificar_usuario",),
            "auditoria": ("registrar_falha_biometrica",),
        }
        modulos = {}
        funcoes = []
        for nome, atributos in membros.items():
            modulo = ModuleType(nome)
            for atributo in atributos:
                funcao = Mock(side_effect=AssertionError("Operação inesperada"))
                setattr(modulo, atributo, funcao)
                funcoes.append(funcao)
            modulos[nome] = modulo
        with patch.dict(sys.modules, modulos):
            for arquivo in ("cadastro_biometria.py", "controle_acesso.py"):
                with self.subTest(arquivo=arquivo):
                    runpy.run_path(str(RAIZ / arquivo), run_name="__main__")
        for funcao in funcoes:
            funcao.assert_not_called()

    def test_experimento_exige_parametros_antes_de_importar_dependencias(self):
        bloqueados = {nome: None for nome in (
            "cv2", "numpy", "mysql", "mysql.connector", "insightface", "insightface.app")}
        casos = [([], 2), (["--help"], 0), (["--imagem", "sintetica.jpg"], 2),
                 (["--usuario", "7"], 2),
                 (["--imagem", "sintetica.jpg", "--usuario", "abc"], 2)]
        with patch.dict(sys.modules, bloqueados), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            for argumentos, codigo in casos:
                with self.subTest(argumentos=argumentos), patch.object(
                        sys, "argv", [str(EXPERIMENTO), *argumentos]):
                    with self.assertRaises(SystemExit) as erro:
                        runpy.run_path(str(EXPERIMENTO), run_name="__main__")
                    self.assertEqual(erro.exception.code, codigo)

    def test_experimento_parametrizado_preserva_persistencia_e_serializacao(self):
        vetor = np.arange(512, dtype=np.float32)
        cv2 = ModuleType("cv2")
        cv2.imread = Mock(return_value=object())
        mysql = ModuleType("mysql")
        connector = ModuleType("mysql.connector")
        connector.connect = Mock()
        mysql.connector = connector
        conexao = connector.connect.return_value
        banco = ModuleType("banco")
        banco.conectar_banco = Mock(return_value=conexao)
        cursor = conexao.cursor.return_value
        cursor.lastrowid = 42
        cursor.fetchone.return_value = (vetor.tobytes(),)
        insightface = ModuleType("insightface")
        app = ModuleType("insightface.app")
        app.FaceAnalysis = Mock()
        insightface.app = app
        modelo = app.FaceAnalysis.return_value
        modelo.get.return_value = [SimpleNamespace(normed_embedding=vetor)]
        with patch.dict(sys.modules, {
            "cv2": cv2, "mysql": mysql, "mysql.connector": connector,
            "banco": banco,
            "insightface": insightface, "insightface.app": app,
        }), patch.object(sys, "argv", [str(EXPERIMENTO), "--imagem", "pasta/ref.jpg", "--usuario", "7"]), \
                contextlib.redirect_stdout(io.StringIO()) as saida:
            runpy.run_path(str(EXPERIMENTO), run_name="__main__")
        cv2.imread.assert_called_once_with("pasta/ref.jpg")
        banco.conectar_banco.assert_called_once_with()
        connector.connect.assert_not_called()
        app.FaceAnalysis.assert_called_once_with(name="buffalo_l", providers=["CPUExecutionProvider"])
        modelo.prepare.assert_called_once_with(ctx_id=-1, det_size=(640, 640))
        insercao, consulta = cursor.execute.call_args_list
        self.assertIn("INSERT INTO biometria_facial", insercao.args[0])
        self.assertEqual(insercao.args[1], (7, vetor.tobytes(), "buffalo_l", 512))
        self.assertEqual(len(insercao.args[1][1]), 2048)
        self.assertIn("WHERE id_biometria = %s", consulta.args[0])
        self.assertEqual(consulta.args[1], (42,))
        conexao.commit.assert_called_once_with()
        conexao.rollback.assert_not_called()
        cursor.close.assert_called_once_with()
        conexao.close.assert_called_once_with()
        self.assertIn("Embeddings idênticos: True", saida.getvalue())

if __name__ == "__main__":
    unittest.main()
