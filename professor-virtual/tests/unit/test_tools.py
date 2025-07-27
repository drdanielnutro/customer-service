import pytest
from professor_virtual.tools import (
    transcrever_audio,
    analisar_necessidade_visual,
    analisar_imagem_educacional,
    gerar_audio_tts,
)


class FakeArtifact:
    def __init__(self, name, content):
        self.name = name
        self.content = content


class FakeSession:
    def __init__(self):
        self.artifacts = {}

    def get_artifact(self, name):
        return self.artifacts.get(name)

    def create_artifact(self, name, content, mime_type=None):
        self.artifacts[name] = FakeArtifact(name, content)


class FakeToolContext:
    def __init__(self, session):
        self.session = session


def test_transcrever_audio():
    session = FakeSession()
    session.artifacts["pergunta.wav"] = FakeArtifact("pergunta.wav", b"0" * 16000)
    ctx = FakeToolContext(session)
    result = transcrever_audio("pergunta.wav", ctx)
    assert result["sucesso"]
    assert "texto" in result


def test_analisar_necessidade_visual():
    ctx = FakeToolContext(FakeSession())
    texto = "Olhe essa figura aqui"
    result = analisar_necessidade_visual(texto, ctx)
    assert result["necessita_imagem"]


def test_analisar_imagem_educacional():
    session = FakeSession()
    session.artifacts["exercicio.png"] = FakeArtifact("exercicio.png", b"1" * 20000)
    ctx = FakeToolContext(session)
    result = analisar_imagem_educacional("exercicio.png", "qual é a resposta?", ctx)
    assert result["sucesso"]
    assert result["qualidade_adequada"] in (True, False)


def test_gerar_audio_tts():
    session = FakeSession()
    ctx = FakeToolContext(session)
    result = gerar_audio_tts("Olá", ctx)
    assert result["sucesso"]
    assert result["nome_artefato_gerado"] in session.artifacts

