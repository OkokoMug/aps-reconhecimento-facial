import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]

class ImportacaoExperimentos(unittest.TestCase):
    def test_importacao_sem_bibliotecas_externas_ou_io(self):
        nomes = ("teste_arcface", "avaliador_embeddings", "teste_banco_embedding")
        with patch.dict(sys.modules), patch.object(sys, "path", [str(RAIZ), *sys.path]):
            for nome in list(sys.modules):
                if nome == "experimentos" or nome.startswith("experimentos."):
                    del sys.modules[nome]
            with patch.dict(sys.modules, {
                "cv2": None, "numpy": None, "mysql": None,
                "mysql.connector": None, "insightface": None,
                "insightface.app": None,
            }), patch("builtins.open", side_effect=AssertionError("Arquivo aberto")), \
                    patch.object(Path, "iterdir", side_effect=AssertionError("Diretório lido")), \
                    patch("builtins.print") as imprimir:
                for nome in nomes:
                    with self.subTest(modulo=nome):
                        modulo = importlib.import_module(f"experimentos.{nome}")
                        self.assertTrue(callable(modulo.main))
                        self.assertEqual(modulo.PASTA_IMAGENS, RAIZ / "imagens")
                        self.assertEqual(Path(modulo.__file__).parent, RAIZ / "experimentos")
                imprimir.assert_not_called()

    def test_arquivos_de_imagem_continuam_disponiveis(self):
        #Verifica apenas existência, não carrega as imagens!
        nomes = ("pessoa_A_01.jpg", "pessoa_A_02.jpg", "pessoa_B_01.jpg")
        ausentes = [nome for nome in nomes if not (RAIZ / "imagens" / nome).is_file()]
        if ausentes:
            self.skipTest("Imagens dos experimentos indisponíveis: " + ", ".join(ausentes))
        for nome in nomes:
            with self.subTest(imagem=nome):
                self.assertTrue((RAIZ / "imagens" / nome).is_file())

if __name__ == "__main__":
    unittest.main()
