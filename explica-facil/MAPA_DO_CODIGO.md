# Como o código do Explica Fácil está organizado

## O percurso de uma página

```text
Utilizador abre um endereço no navegador
                ↓
urls.py encontra a função correspondente
                ↓
views.py verifica o perfil e prepara os dados
                ↓
models.py permite consultar o MySQL
                ↓
template HTML recebe os dados e apresenta a página
```

Para alterar dados, a página chama também as regras de `services.py`.

## Um exemplo completo de inscrição

1. O aluno abre `sessoes/1/`. O número identifica uma sessão.
2. A rota em `explicacoes/urls.py` chama `detalhe`, em `views.py`.
3. A função procura a sessão no MySQL e envia-a ao template `detalhe.html`.
4. O template apresenta o formulário **Confirmar a minha inscrição**.
5. O botão envia um pedido POST à rota `sessoes/1/inscrever/`.
6. A função `inscrever` da página verifica se a pessoa é aluno e chama `services.inscrever`.
7. O serviço bloqueia temporariamente os registos do aluno e da sessão enquanto verifica as condições.
8. Verifica a data, o estado, a capacidade, a duplicação e os conflitos de horário.
9. Guarda a inscrição e a notificação numa transação: ou ficam ambas guardadas, ou a operação é revertida.
10. A página apresenta a confirmação. O plano passa a mostrar a ocupação atualizada.

O bloqueio é importante quando dois alunos tentam ocupar o último lugar ao mesmo tempo. Mostrar o botão desativado ajuda o utilizador, mas a verificação decisiva tem de acontecer no servidor.

## Ficheiros principais

| Ficheiro | O que deves procurar |
| --- | --- |
| `manage.py` | O início dos comandos de gestão, como testes e migrações |
| `config/settings.py` | Configuração da base de dados, idioma, fuso horário e regras fixas |
| `config/urls.py` | Endereços principais, entrada, saída e painel de gestão |
| `explicacoes/models.py` | As classes que representam os dados |
| `explicacoes/forms.py` | Campos, validação dos formulários e registo de alunos |
| `explicacoes/views.py` | A função que responde a cada página |
| `explicacoes/services.py` | Regras de inscrição, cancelamento, horários e avisos |
| `explicacoes/admin.py` | Gestão de utilizadores e disciplinas no painel Django |
| `explicacoes/urls.py` | Endereços das funcionalidades do projeto |
| `templates/base.html` | Cabeçalho, navegação e rodapé comuns |
| `templates/explicacoes/plano.html` | Plano semanal e cartões das sessões |
| `static/css/style.css` | Cores, tamanhos, organização e adaptação ao telemóvel |
| `explicacoes/migrations/0001_initial.py` | Instruções que criam as tabelas |
| `explicacoes/tests/` | Exemplos automáticos que verificam os comportamentos |

## As sete classes dos dados

**Utilizador:** guarda o email, o nome e o perfil. Herda ferramentas de autenticação do Django. A palavra-passe é guardada através do mecanismo de proteção do Django.

**Disciplina:** representa Matemática, Português ou outra disciplina.

**ProfessorDisciplina:** associa um professor às disciplinas que pode lecionar. Resolve uma relação de vários professores para várias disciplinas.

**Disponibilidade:** representa um intervalo semanal do professor, por exemplo segunda-feira das 09h às 12h.

**Sessao:** representa uma explicação numa data concreta. O início e o fim permitem verificar a duração e os conflitos.

**Inscricao:** liga um aluno a uma sessão. O estado distingue inscrições ativas de canceladas. A combinação aluno e sessão é única.

**Notificacao:** guarda uma mensagem dirigida a uma pessoa e, quando aplicável, ligada a uma sessão.

## Palavras de Python e Django que vais encontrar

- `class`: define uma classe, como `Sessao`.
- `def`: define uma função, como `inscrever`.
- `if`: executa uma ação se a condição for verdadeira.
- `for`: percorre vários elementos, como as sessões de uma semana.
- `return`: devolve o resultado de uma função.
- `ForeignKey`: liga um registo a outro, por exemplo uma sessão ao professor.
- `objects.filter(...)`: procura registos que cumprem condições.
- `get_object_or_404(...)`: procura um registo e apresenta uma página de não encontrado se ele não existir.
- `request.GET`: contém os filtros enviados no endereço.
- `request.POST`: contém os campos enviados por um formulário.
- `render(...)`: combina os dados com uma página HTML.
- `redirect(...)`: encaminha para outro endereço.
- `@login_required`: exige uma conta autenticada.
- `@perfil(...)`: exige um dos perfis do projeto.
- `@transaction.atomic`: confirma as alterações em conjunto ou reverte-as em caso de falha.
- `select_for_update()`: bloqueia registos durante uma transação para coordenar alterações simultâneas.

## Como os templates mostram os dados

```django
{{ sessao.disciplina.nome }}
```

Mostra o nome da disciplina de uma sessão.

```django
{% for sessao in sessoes %}
    <p>{{ sessao.disciplina.nome }}</p>
{% endfor %}
```

Repete um parágrafo por cada sessão.

```django
{% if sessao.vagas %}
    <p>Ainda existem lugares.</p>
{% endif %}
```

Mostra o texto quando existem vagas. Esta condição visual não substitui a validação no serviço.

## Como a estrutura da base é criada

Os modelos são escritos em Python. Uma migração descreve as alterações às tabelas. O comando `migrate`, executado automaticamente no arranque, aplica as migrações ao MySQL.

Se alterares um modelo, os passos normais são:

```sh
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test --noinput
```

Uma alteração num texto HTML ou numa cor CSS não precisa de migração.

## Correspondência com os casos de uso

| Caso | Implementação principal |
| --- | --- |
| UC01 Registar aluno | `RegistoForm` e `registo` |
| UC02 Iniciar e terminar sessão | Vistas de autenticação Django e `LoginEmailForm` |
| UC03 Consultar plano semanal | `plano` e `plano.html` |
| UC04 Inscrever numa sessão | `services.inscrever` |
| UC05 Consultar e cancelar inscrições | `minhas_inscricoes` e `cancelar_inscricao` |
| UC06 Gerir disponibilidade | `disponibilidades`, `guardar_disponibilidade` e `apagar_disponibilidade` |
| UC07 Consultar sessões e alunos | `sessoes_professor` |
| UC08 Gerir utilizadores | `UtilizadorAdmin` no painel Django |
| UC09 Gerir disciplinas e professores | `DisciplinaAdmin` e o formulário das associações |
| UC10 Criar e editar sessões | `SessaoForm` e `guardar_sessao` |
| UC11 Cancelar sessão | `cancelar_sessao` |
| UC12 Enviar aviso | `AvisoForm` e `enviar_aviso` |
| UC13 Consultar notificações | `notificacoes` e `ler_notificacao` |

## Uma explicação curta para a apresentação

O site usa Django para receber os pedidos, verificar permissões e trabalhar com a base de dados. As páginas HTML apresentam os dados e o CSS define o aspeto. As regras de inscrição estão separadas dos ecrãs para serem mais fáceis de encontrar e testar. A base MySQL mantém os dados, e o Docker prepara o ambiente de execução.
