# Testes automatizados

Executar a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py' -v
```

Usar a descoberta restrita a `tests/`. Os scripts manuais estão em `experimentos/`
e suas importações não executam os experimentos.

A suíte utiliza `unittest`, `unittest.mock` e NumPy.
Os módulos de produção são carregados em cópias isoladas com OpenCV, MySQL e InsightFace substituídos antes da importação.

São caracterizados similaridade por produto escalar, máximo por usuário, empates, threshold 0.30, referências inválidas, extração simulada, serialização float32 de 2.048 bytes, cadastro, auditoria, chamada da procedure e caminhos transacionais.
Na fronteira exata 0.30, o produto escalar é simulado para evitar a diferença de representação entre float32 e float Python. Os testes acima usam NumPy.

Limitações: não valida inferência real, qualidade biométrica, hardware e teclas da webcam, interface interativa, implementação interna da procedure, esquema MySQL, persistência real, concorrência ou todas as falhas possíveis de abertura e fechamento de recursos.
