import cv2
import numpy as np
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(ctx_id=-1, det_size=(640, 640))

class ErroDeteccaoFacial(ValueError):
    """Representa uma captura com quantidade inválida de rostos."""
    pass

def extrair_embedding_frame(imagem):

    if imagem is None or imagem.size == 0:
        raise ValueError("Imagem inválida.")

    faces = app.get(imagem)

    if len(faces) == 0:
        raise ErroDeteccaoFacial(
            "Nenhuma face detectada"
        )

    if len(faces) > 1:
        raise ErroDeteccaoFacial(
            "Múltiplas faces detectadas"
        )

    embedding = faces[0].normed_embedding.astype(np.float32)

    if embedding.shape != (512,):
        raise ValueError(
            f"Dimensão inesperada: {embedding.shape}"
        )

    if not np.isfinite(embedding).all():
        raise ValueError("Embedding extraído contém valores não finitos.")

    norma = np.linalg.norm(embedding.astype(np.float64))
    if not np.isclose(norma, 1.0, rtol=0.0, atol=1e-5):
        raise ValueError("Embedding extraído não possui norma unitária.")

    return embedding

def extrair_embedding(caminho_imagem):

    imagem = cv2.imread(caminho_imagem)

    if imagem is None:
        raise ValueError(
            f"Não foi possível carregar: {caminho_imagem}"
        )

    return extrair_embedding_frame(imagem)
