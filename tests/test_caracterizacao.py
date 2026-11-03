import importlib.util
from itertools import permutations
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]

class Caracterizacao(unittest.TestCase):
    def setUp(self):
        #Carrega cópias isoladas dos módulos, sem importar bibliotecas de Input e Output.
        cv2 = ModuleType("cv2")
        cv2.imread = Mock(side_effect=AssertionError("Leitura real proibida"))
        cv2.VideoCapture = Mock(side_effect=AssertionError("Webcam proibida"))
        mysql = ModuleType("mysql")
        connector = ModuleType("mysql.connector")
        connector.connect = Mock(side_effect=AssertionError("MySQL real proibido"))
        mysql.connector = connector
        insightface = ModuleType("insightface")
        face_app = ModuleType("insightface.app")
        face_app.FaceAnalysis = Mock()
        insightface.app = face_app
        self.face_factory = face_app.FaceAnalysis
        self.addCleanup(patch.stopall)
        patch("builtins.print").start()
        patch.dict(sys.modules, {
            "cv2": cv2, "mysql": mysql, "mysql.connector": connector,
            "insightface": insightface, "insightface.app": face_app,
        }).start()
        self.modulo_banco = self.carregar("banco")
        self.processamento = self.carregar("processamento_facial")
        self.repositorio = self.carregar("repositorio_biometrias")
        self.cadastro = self.carregar("cadastro_biometria")
        self.identificacao = self.carregar("identificacao_facial")
        self.auditoria = self.carregar("auditoria")
        self.controle = self.carregar("controle_acesso")
        self.captura = self.carregar("captura_webcam")
        self.sistema = self.carregar("sistema_acesso")
        self.conexao = Mock()
        self.cursor = self.conexao.cursor.return_value

    def carregar(self, nome):
        spec = importlib.util.spec_from_file_location(nome, RAIZ / f"{nome}.py")
        modulo = importlib.util.module_from_spec(spec)
        patch.dict(sys.modules, {nome: modulo}).start()
        spec.loader.exec_module(modulo)
        return modulo

    def banco(self, modulo):
        return patch.object(modulo, "conectar_banco", return_value=self.conexao).start()

    def fechados(self):
        self.cursor.close.assert_called_once_with()
        self.conexao.close.assert_called_once_with()

    @staticmethod
    def vetor(score=1.0):
        vetor = np.zeros(512, dtype=np.float32)
        vetor[0] = score
        vetor[1] = np.sqrt(1 - score ** 2)
        return vetor

    def identificar(self, registros):
        self.banco(self.identificacao)
        self.cursor.fetchall.return_value = registros
        patch.object(self.identificacao, "extrair_embedding_frame",
                     return_value=self.vetor()).start()
        return self.identificacao.identificar_usuario(frame=object())

    def test_configuracao_modelo(self):
        self.face_factory.assert_called_once_with(
            name="buffalo_l", providers=["CPUExecutionProvider"])
        self.cadastro.app.prepare.assert_called_once_with(ctx_id=-1, det_size=(640, 640))
        self.assertIs(self.cadastro.conectar_banco, self.modulo_banco.conectar_banco)
        for nome in ("app", "ErroDeteccaoFacial", "extrair_embedding", "extrair_embedding_frame"):
            self.assertIs(getattr(self.cadastro, nome), getattr(self.processamento, nome))
        self.assertIs(self.sistema.ErroDeteccaoFacial, self.processamento.ErroDeteccaoFacial)

    def test_similaridade_maxima_por_usuario_nao_media(self):
        registros = [(1, self.vetor(.2).tobytes(), 512),
                     (1, self.vetor(.9).tobytes(), 512),
                     (2, self.vetor(.8).tobytes(), 512)]
        usuario, score = self.identificar(registros)
        self.assertEqual(usuario, 1)
        self.assertAlmostEqual(score, .9, places=6)
        sql, parametros = self.cursor.execute.call_args.args
        self.assertIn("WHERE ativo = 1", sql)
        self.assertIn("AND modelo = %s", sql)
        self.assertEqual(parametros, ("buffalo_l",))
        self.fechados()

    def test_threshold_real_abaixo_e_acima(self):
        self.assertEqual(self.identificacao.THRESHOLD, .30)
        for score, aceito in [(.2999, False), (.3001, True)]:
            with self.subTest(score=score):
                resultado = self.identificar([(1, self.vetor(score).tobytes(), 512)])
                self.assertEqual(resultado is not None, aceito)

    def test_threshold_exatamente_igual_e_aceito(self):
        # isola o produto escalar para caracterizar a comparação de fronteira.
        with patch.object(self.identificacao.np, "dot", return_value=.30):
            self.assertEqual(self.identificar([(1, self.vetor().tobytes(), 512)]), (1, .30))

    def test_empate_preserva_primeiro_usuario_lido(self):
        blob = self.vetor().tobytes()
        self.assertEqual(self.identificar([(8, blob, 512), (2, blob, 512)])[0], 8)

    def test_maximo_por_usuario_independe_da_ordem_das_referencias(self):
        # Inclui [0.9, 0.2] e [0.2, 0.9], e todas as posições do concorrente.
        registros = [(1, self.vetor(.9).tobytes(), 512),
                     (1, self.vetor(.2).tobytes(), 512),
                     (2, self.vetor(.8).tobytes(), 512)]
        for ordem in permutations(registros):
            with self.subTest(ordem=[(r[0], float(np.frombuffer(r[1], dtype=np.float32)[0]))
                                     for r in ordem]):
                usuario, score = self.identificar(list(ordem))
                self.assertEqual(usuario, 1)
                self.assertAlmostEqual(score, .9, places=6)

    def test_threshold_vizinhos_float32_com_produto_escalar_real(self):
        centro = np.float32(.30)
        abaixo = np.nextafter(centro, np.float32(-np.inf))
        acima = np.nextafter(centro, np.float32(np.inf))
        self.assertLess(float(abaixo), .30)
        self.assertGreater(float(centro), .30)
        for valor, aceito in ((abaixo, False), (centro, True), (acima, True)):
            with self.subTest(score=float(valor)):
                resultado = self.identificar([(1, self.vetor(float(valor)).tobytes(), 512)])
                if aceito:
                    self.assertEqual(resultado, (1, float(valor)))
                else:
                    self.assertIsNone(resultado)
        # A igualdade matemática é verificada separadamente com dot simulado:
        # nenhum float32 representa exatamente o número decimal 0.30.

    def test_empate_multiplas_referencias_preserva_primeiro_usuario(self):
        for primeiro, segundo in ((8, 2), (2, 8)):
            for scores in ((.9, .2), (.2, .9)):
                with self.subTest(primeiro=primeiro, scores=scores):
                    registros = [(primeiro, self.vetor(scores[0]).tobytes(), 512),
                                 (segundo, self.vetor(.9).tobytes(), 512),
                                 (primeiro, self.vetor(scores[1]).tobytes(), 512),
                                 (segundo, self.vetor(.1).tobytes(), 512)]
                    usuario, score = self.identificar(registros)
                    self.assertEqual(usuario, primeiro)
                    self.assertAlmostEqual(score, .9, places=6)

    def exigir_rejeicao_referencia(self, valor):
        # Fixture tem formato válido, mas conteúdo inválido. Consulta é unitária.
        # Não usa mock de dot nem adapta o esperado ao comportamento observado.
        referencia = np.zeros(512, dtype=np.float32)
        referencia[0] = valor
        self.assertEqual(referencia.shape, (512,))
        self.assertEqual(len(referencia.tobytes()), 2048)
        with np.errstate(invalid="ignore", over="ignore"):
            resultado = self.identificar([(7, referencia.tobytes(), 512)])
        self.assertIsNone(resultado, "Referência inválida não pode identificar usuário")

    def test_referencia_nan_deve_ser_rejeitada(self):
        self.exigir_rejeicao_referencia(np.nan)

    def test_referencia_infinito_positivo_deve_ser_rejeitada(self):
        self.exigir_rejeicao_referencia(np.inf)

    def test_referencia_infinito_negativo_deve_ser_rejeitada(self):
        self.exigir_rejeicao_referencia(-np.inf)

    def test_referencia_nula_deve_ser_rejeitada(self):
        self.exigir_rejeicao_referencia(0.)

    def test_referencia_norma_dois_deve_ser_rejeitada(self):
        # Norma 2, não um erro de arredondamento de um vetor unitário.
        self.exigir_rejeicao_referencia(2.)

    def test_sem_referencias_ou_apenas_invalidas(self):
        for registros in [[], [(1, b"curto", 512)],
                          [(1, self.vetor().tobytes(), 128)]]:
            with self.subTest(registros=len(registros)):
                self.assertIsNone(self.identificar(registros))

    def test_referencia_invalida_nao_impede_valida(self):
        self.assertEqual(self.identificar([
            (1, b"curto", 512), (2, self.vetor().tobytes(), 512)])[0], 2)

    def test_conteudo_invalido_nao_impede_outras_referencias_validas(self):
        for valor in (np.nan, np.inf, -np.inf, 0., 2.):
            for mesmo_usuario in (False, True):
                for invalida_primeiro in (False, True):
                    with self.subTest(valor=valor, mesmo_usuario=mesmo_usuario,
                                      invalida_primeiro=invalida_primeiro):
                        vetor = np.zeros(512, dtype=np.float32)
                        vetor[0] = valor
                        invalida = (2 if mesmo_usuario else 1, vetor.tobytes(), 512)
                        valida = (2, self.vetor(.8).tobytes(), 512)
                        registros = [invalida, valida] if invalida_primeiro else [valida, invalida]
                        usuario, score = self.identificar(registros)
                        self.assertEqual(usuario, 2)
                        self.assertAlmostEqual(score, .8, places=6)

    def test_exige_exatamente_uma_fonte(self):
        for argumentos in [{}, {"frame": object(), "caminho_imagem": "sintetica"}]:
            with self.subTest(argumentos=list(argumentos)):
                with self.assertRaises(ValueError):
                    self.identificacao.identificar_usuario(**argumentos)

    def test_extracao_converte_float32_sem_renormalizar(self):
        original = np.zeros(512, dtype=np.float64)
        original[:2] = (.6, .8)
        self.assertTrue(np.isfinite(original).all())
        self.assertAlmostEqual(np.linalg.norm(original), 1.0, places=14)
        self.cadastro.app.get.return_value = [SimpleNamespace(normed_embedding=original)]
        resultado = self.cadastro.extrair_embedding_frame(np.ones((2, 2, 3)))
        self.assertEqual(resultado.shape, (512,))
        self.assertEqual(resultado.dtype, np.float32)
        np.testing.assert_array_equal(resultado, original.astype(np.float32))
        self.assertEqual(resultado.tobytes(), original.astype(np.float32).tobytes())

    def test_quantidade_faces_e_dimensao(self):
        for faces in [[], [Mock(), Mock()]]:
            self.cadastro.app.get.return_value = faces
            with self.assertRaises(self.cadastro.ErroDeteccaoFacial):
                self.cadastro.extrair_embedding_frame(np.ones((2, 2, 3)))
        self.cadastro.app.get.return_value = [SimpleNamespace(normed_embedding=np.zeros(128))]
        with self.assertRaisesRegex(ValueError, "Dimensão inesperada"):
            self.cadastro.extrair_embedding_frame(np.ones((2, 2, 3)))

    def test_cadastro_serializa_bytes_float32(self):
        self.banco(self.cadastro)
        self.cursor.fetchone.return_value = (7,)
        vetor = self.vetor(.75)
        patch.object(self.cadastro, "extrair_embedding", return_value=vetor).start()
        self.cadastro.cadastrar_biometria(7, "imagem_sintetica")
        sql, parametros = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO biometria_facial", sql)
        usuario, blob, modelo, dimensao = parametros
        self.assertEqual((usuario, modelo, dimensao), (7, "buffalo_l", 512))
        self.assertEqual(len(blob), 2048)
        self.assertEqual(blob, vetor.tobytes())
        np.testing.assert_array_equal(np.frombuffer(blob, dtype=np.float32), vetor)
        self.conexao.commit.assert_called_once_with()
        self.conexao.rollback.assert_not_called()
        self.fechados()

    def test_cadastro_usuario_inexistente_rollback(self):
        self.banco(self.cadastro)
        self.cursor.fetchone.return_value = None
        with patch.object(self.cadastro, "extrair_embedding") as extrair:
            with self.assertRaisesRegex(ValueError, "não encontrado"):
                self.cadastro.cadastrar_biometria(7, "sintetica")
            extrair.assert_not_called()
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_called_once_with()
        self.fechados()

    def test_cadastro_erro_insercao_rollback_e_mesmo_cursor(self):
        self.banco(self.cadastro)
        self.cursor.fetchone.return_value = (7,)
        erro = RuntimeError("inserção simulada falhou")
        self.cursor.execute.side_effect = [None, erro]
        with patch.object(self.cadastro, "extrair_embedding", return_value=self.vetor()):
            with self.assertRaises(RuntimeError) as contexto:
                self.cadastro.cadastrar_biometria(7, "sintetica")
        self.assertIs(contexto.exception, erro)
        self.conexao.cursor.assert_called_once_with()
        consulta, insercao = self.cursor.execute.call_args_list
        self.assertEqual(consulta.args[1], (7,))
        self.assertIn("SELECT id_usuario", consulta.args[0])
        self.assertIn("INSERT INTO biometria_facial", insercao.args[0])
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_called_once_with()
        self.fechados()

    def test_identificacao_erro_leitura_fecha_sem_transacao(self):
        self.banco(self.identificacao)
        erro = RuntimeError("leitura simulada falhou")
        self.cursor.fetchall.side_effect = erro
        with patch.object(self.identificacao, "extrair_embedding_frame", return_value=self.vetor()):
            with self.assertRaises(RuntimeError) as contexto:
                self.identificacao.identificar_usuario(frame=object())
        self.assertIs(contexto.exception, erro)
        self.conexao.cursor.assert_called_once_with()
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_not_called()
        self.fechados()

    def test_auditoria_area_existente_ou_inexistente(self):
        self.banco(self.auditoria)
        for registro, area in [((4,), 4), (None, None)]:
            with self.subTest(area=area):
                self.conexao.reset_mock()
                self.cursor.fetchone.return_value = registro
                self.auditoria.registrar_falha_biometrica(4, "Nenhuma face detectada")
                chamadas = self.cursor.execute.call_args_list
                self.assertEqual(len(chamadas), 2)
                self.assertEqual(chamadas[0].args[1], (4,))
                sql, parametros = chamadas[1].args
                self.assertEqual(" ".join(sql.split()),
                    "INSERT INTO registro_acesso ( id_usuario, id_area, id_area_solicitada, "
                    "resultado, confianca, motivo ) VALUES ( NULL, %s, %s, 'NEGADO', NULL, %s )")
                self.assertEqual(parametros, (area, 4, "Nenhuma face detectada"))
                self.conexao.commit.assert_called_once_with()
                self.conexao.rollback.assert_not_called()
                self.fechados()

    def test_auditoria_erro_propaga_e_rollback(self):
        self.banco(self.auditoria)
        erro = RuntimeError("falha simulada")
        self.cursor.execute.side_effect = erro
        with self.assertRaises(RuntimeError) as contexto:
            self.auditoria.registrar_falha_biometrica(4, "motivo")
        self.assertIs(contexto.exception, erro)
        self.conexao.rollback.assert_called_once_with()
        self.conexao.commit.assert_not_called()
        self.fechados()

    def preparar_autorizacao(self, resposta):
        conectar = self.banco(self.controle)
        patch.object(self.controle, "identificar_usuario", return_value=(7, .876543)).start()
        self.auditar = patch.object(self.controle, "registrar_falha_biometrica").start()
        resultado = Mock()
        resultado.fetchone.return_value = resposta
        self.cursor.stored_results.return_value = [resultado]
        return conectar

    def test_procedure_argumentos_retorno_e_sem_auditoria_duplicada(self):
        for decisao in ["PERMITIDO", "NEGADO"]:
            with self.subTest(decisao=decisao):
                self.conexao.reset_mock()
                resposta = dict(usuario="Sintetico", area="Teste", resultado=decisao, motivo="teste")
                self.preparar_autorizacao(resposta)
                frame = object()
                self.assertIs(self.controle.solicitar_acesso(4, frame=frame), resposta)
                self.controle.identificar_usuario.assert_called_once_with(caminho_imagem=None, frame=frame)
                self.conexao.cursor.assert_called_once_with(dictionary=True)
                self.cursor.callproc.assert_called_once_with("verificar_acesso", (7, 4, .8765))
                self.conexao.commit.assert_called_once_with()
                self.conexao.rollback.assert_not_called()
                self.auditar.assert_not_called()
                self.fechados()

    def test_desconhecido_audita_e_nao_chama_procedure(self):
        conectar = self.preparar_autorizacao(None)
        self.controle.identificar_usuario.return_value = None
        self.assertIsNone(self.controle.solicitar_acesso(4, caminho_imagem="sintetica"))
        self.auditar.assert_called_once_with(id_area_solicitada=4, motivo="Identidade não reconhecida")
        conectar.assert_not_called()
        self.cursor.callproc.assert_not_called()

    def test_procedure_erro_rollback_e_fechamento(self):
        self.preparar_autorizacao(None)
        erro = RuntimeError("procedure falhou")
        self.cursor.callproc.side_effect = erro
        with self.assertRaises(RuntimeError) as contexto:
            self.controle.solicitar_acesso(4, frame=object())
        self.assertIs(contexto.exception, erro)
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_called_once_with()
        self.fechados()

    def test_procedure_sem_resultado_commit_antes_do_erro(self):
        self.preparar_autorizacao(None)
        with self.assertRaisesRegex(RuntimeError, "não retornou um resultado"):
            self.controle.solicitar_acesso(4, frame=object())
        # Caracteriza a ordem atual, sem recomendar essa política transacional.
        self.assertEqual(self.conexao.method_calls,
                         [call.cursor(dictionary=True), call.commit(), call.rollback(), call.close()])
        self.fechados()

    def test_auxiliar_le_uma_linha_por_resultado_e_retorna_ultimo(self):
        primeiro, ultimo = Mock(), Mock()
        resposta = {"resultado": "NEGADO"}
        ultimo.fetchone.return_value = resposta
        self.cursor.stored_results.return_value = iter([primeiro, ultimo])
        self.assertIs(self.controle._executar_verificar_acesso(
            self.cursor, 7, 4, .876543), resposta)
        self.assertEqual(self.cursor.method_calls, [
            call.callproc("verificar_acesso", (7, 4, .8765)), call.stored_results()])
        primeiro.fetchone.assert_called_once_with()
        ultimo.fetchone.assert_called_once_with()
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_not_called()
        self.conexao.close.assert_not_called()

    def test_auxiliar_sem_resultados_ou_ultima_linha_vazia(self):
        vazio = Mock()
        vazio.fetchone.return_value = None
        for resultados in [[], [Mock(), vazio]]:
            with self.subTest(quantidade=len(resultados)):
                self.cursor.stored_results.return_value = resultados
                self.assertIsNone(self.controle._executar_verificar_acesso(
                    self.cursor, 7, 4, .8))
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_not_called()
        self.cursor.close.assert_not_called()

    def test_erro_leitura_procedure_propaga_rollback_e_fecha(self):
        self.preparar_autorizacao(None)
        erro = RuntimeError("leitura do resultado falhou")
        self.cursor.stored_results.return_value[0].fetchone.side_effect = erro
        with self.assertRaises(RuntimeError) as contexto:
            self.controle.solicitar_acesso(4, frame=object())
        self.assertIs(contexto.exception, erro)
        self.conexao.commit.assert_not_called()
        self.conexao.rollback.assert_called_once_with()
        self.fechados()

if __name__ == "__main__":
    unittest.main()
