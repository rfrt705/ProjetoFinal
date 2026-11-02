# Explica Fácil

Site de gestão de explicações para um projeto final de formação.

**Começa pelo [guia passo a passo](GUIA_PASSO_A_PASSO.md).** Foi escrito para quem está a iniciar a aprendizagem.

## O que faz

- Registo de alunos e entrada com email e palavra-passe.
- Perfis de aluno, professor e administrador.
- Plano semanal com filtros por disciplina e professor.
- Sessões de uma hora, numa data concreta, com um a três alunos.
- Inscrições, cancelamentos e proteção contra conflitos e pedidos simultâneos.
- Disponibilidade dos professores e gestão de sessões.
- Avisos dentro do site, sem envio de email nesta versão.
- Administração de utilizadores, disciplinas e associações professor–disciplina.

Os horários de exemplo são de segunda a sexta, às 09h, 10h, 11h, 14h, 15h, 16h e 17h. São configuráveis no `.env` e precisam de ser ajustados ao horário aprovado para o projeto.

## Arranque

Precisas do Docker Desktop aberto e do Python 3 no computador. As bibliotecas do site são instaladas no contentor, sem instalação manual no computador.

```sh
python iniciar.py
docker compose exec web python manage.py preparar_demo
```

Em macOS, o primeiro comando pode ser `python3 iniciar.py`; em Windows, `py iniciar.py`.

Abre [o site local](http://localhost:8008/).

## Contas fictícias

As contas só existem depois de executar `preparar_demo`.

| Perfil | Email | Palavra-passe inicial |
| --- | --- | --- |
| Administrador | admin@explicafacil.test | Aprender2026! |
| Professor | ana@explicafacil.test | Aprender2026! |
| Aluno | aluno1@explicafacil.test | Aprender2026! |

São contas de demonstração local, sem endereços reais de envio. O comando não apaga dados existentes nem repõe palavras-passe de contas que já existam.

## Pastas

```text
explica-facil/
├── config/                Configuração geral e endereços principais
├── explicacoes/           Dados, formulários, páginas e regras do projeto
│   ├── migrations/        Estrutura da base de dados
│   ├── management/        Comandos de demonstração e verificação
│   └── tests/             Testes automáticos
├── templates/             Páginas HTML
├── static/css/            Aspeto visual
├── docker/                Arranque e permissões da base de testes
├── compose.yaml           Liga o site ao MySQL
├── Dockerfile             Prepara o ambiente Python
├── iniciar.py             Ajuda no primeiro arranque
├── manage.py              Executa comandos Django
├── requirements.txt       Bibliotecas e versões
├── .env.example           Exemplo de configuração sem segredos
├── GUIA_PASSO_A_PASSO.md   Tutorial de utilização e aprendizagem
└── MAPA_DO_CODIGO.md       Explicação dos ficheiros e do percurso dos pedidos
```

## Verificações

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py verificar_base_dados
docker compose exec web python manage.py test --noinput
docker compose exec web python manage.py makemigrations --check --dry-run
```

Os testes criam e eliminam uma base separada chamada `test_explica_facil`. Os dados normais ficam em `explica_facil`. Os testes de simultaneidade exigem MySQL.

## Decisões desta versão

- O administrador usa o painel Django para utilizadores e disciplinas. As sessões são geridas nas páginas próprias do site.
- O professor gere a sua disponibilidade; as sessões já criadas não são alteradas silenciosamente por uma mudança de disponibilidade.
- Uma sessão com alunos não permite alterar data, professor ou disciplina. O administrador deve cancelar e criar outra.
- O aluno pode cancelar antes do início. A inscrição cancelada fica no histórico e pode ser reativada se houver vaga.
- A ocupação de zero alunos fica cinzenta, de um ou dois fica verde e de três fica vermelha. O texto acompanha sempre a cor.
- O site é preparado para demonstração local. Publicação online e email precisam de configuração adicional.

## Referências

- [Tutorial oficial do Django](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [Transações no Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)
- [MySQL no Django](https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-notes)
- [Bases de dados com Docker Compose](https://docs.docker.com/guides/databases/)
