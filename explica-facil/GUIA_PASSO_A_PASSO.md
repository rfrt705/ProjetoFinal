# Guia passo a passo do Explica Fácil

Este guia acompanha uma versão funcional do projeto. Não precisas de escrever todos os ficheiros de uma vez: começa por executar e experimentar, depois estuda uma parte de cada vez.

## 1 O que vais construir

Um site para organizar explicações num plano semanal. Cada sessão tem uma disciplina, um professor, uma data e um horário fixo de uma hora. Um aluno inscreve-se só nessa data. O mínimo é um aluno e o máximo é três.

O navegador mostra as páginas. O Django executa o código Python. O MySQL guarda os dados. O Docker permite executar o Django e o MySQL com as bibliotecas necessárias.

## 2 Confirmar as ferramentas

1. Abre o Docker Desktop e espera até indicar que está pronto.
2. Usa um editor de código, por exemplo o VS Code, para abrir a pasta `explica-facil` completa.
3. Abre um terminal nessa pasta. No VS Code, podes usar **Terminal > Novo terminal**.
4. Verifica o Docker:

```sh
docker --version
docker compose version
```

5. Verifica o Python. No Windows:

```sh
py --version
```

No macOS ou Linux:

```sh
python3 --version
```

Se `python` funcionar no teu computador, também podes usá-lo. Só o comando auxiliar de arranque precisa de Python no computador; o Django é instalado dentro do Docker.

**Checkpoint:** consegues ver as versões do Docker, do Compose e do Python.

## 3 Reconhecer a pasta certa

O terminal deve estar na pasta onde estão `manage.py`, `compose.yaml` e `iniciar.py`. Se estiveres numa pasta acima, entra na pasta do projeto:

```sh
cd explica-facil
```

Se já vês os três ficheiros no editor e o terminal já está nessa pasta, não repitas o `cd`.

No Windows, `dir` lista os ficheiros. No macOS/Linux, usa `ls`.

**Checkpoint:** consegues identificar `manage.py` e `compose.yaml`.

## 4 Iniciar o site e a base de dados

No Windows:

```sh
py iniciar.py
```

No macOS/Linux:

```sh
python3 iniciar.py
```

O ficheiro faz quatro coisas: verifica se o Docker está aberto, cria o `.env` com valores locais aleatórios, prepara o ambiente Python e inicia os serviços `web` e `db`. A primeira execução precisa de ligação à internet para descarregar as imagens e bibliotecas.

O `.env` guarda a configuração local. Não precisas de o preencher manualmente na primeira execução e não deves incluí-lo no repositório.

Quando terminar, abre:

```text
http://localhost:8008/
```

Deves ver a página de entrada do Explica Fácil. Ainda não existem contas no primeiro arranque de uma base nova.

**Checkpoint:** a página de entrada abre no navegador.

## 5 Criar os dados de demonstração

No mesmo terminal:

```sh
docker compose exec web python manage.py preparar_demo
```

Este comando cria dados fictícios: três disciplinas, três professores, quatro alunos, um administrador e sessões futuras na semana atual e na seguinte. As ocupações variam para poderes observar todas as cores. Não apaga dados existentes.

| Perfil | Email | Palavra-passe inicial |
| --- | --- | --- |
| Administrador | admin@explicafacil.test | Aprender2026! |
| Professor | ana@explicafacil.test | Aprender2026! |
| Aluno | aluno1@explicafacil.test | Aprender2026! |

Também existem `maria@explicafacil.test`, `sofia@explicafacil.test` e `aluno2`, `aluno3` e `aluno4` no mesmo domínio `@explicafacil.test`. As palavras-passe iniciais são iguais apenas para facilitar esta demonstração.

Se repetires o comando, não são repostas as palavras-passe das contas existentes nem duplicadas as mesmas sessões. Se não houver sessões nesta semana por já ser fim de semana, avança para a semana seguinte.

**Checkpoint:** entras como aluno e vês o plano semanal.

## 6 Experimentar como aluno

1. Entra com `aluno1@explicafacil.test`.
2. Consulta o plano. Usa as setas para mudar de semana.
3. Escolhe uma sessão com vagas.
4. Confirma a disciplina, a data, o professor e a hora.
5. Carrega em **Confirmar a minha inscrição**.
6. Abre **As minhas inscrições** e confirma que a sessão aparece.
7. Abre **Avisos** e lê a confirmação.
8. Experimenta cancelar uma inscrição futura. O site pede confirmação e liberta a vaga.

Não consegues inscrever-te numa sessão cheia, numa sessão passada, numa sessão cancelada ou em dois horários sobrepostos. Os nomes dos outros alunos não aparecem ao aluno.

**Checkpoint:** consegues inscrever-te e cancelar, e a ocupação muda.

## 7 Experimentar como professor

1. Sai da conta do aluno através de **Sair**.
2. Entra com `ana@explicafacil.test`.
3. Em **As minhas sessões**, consulta os alunos inscritos nas tuas sessões.
4. Em **Disponibilidade**, consulta os intervalos semanais.
5. Experimenta adicionar um intervalo que não se sobreponha a outro.

A demonstração já inclui disponibilidade de segunda a sexta, das 09h às 18h. Tentar adicionar outro intervalo dentro desse período será recusado por sobreposição. Para experimentar uma alteração, escolhe um intervalo e usa **Editar**.

O site impede remover ou reduzir disponibilidade necessária para uma sessão futura. Essa sessão deve ser resolvida primeiro pelo administrador.

**Checkpoint:** consegues explicar a diferença entre disponibilidade e sessão. Disponibilidade é um intervalo semanal; sessão é uma aula numa data concreta.

## 8 Experimentar como administrador

1. Sai e entra com `admin@explicafacil.test`.
2. Abre **Utilizadores e disciplinas** para entrar no painel de gestão do Django.
3. Em **Utilizadores**, podes criar professores e alunos e atribuir o perfil.
4. Em **Disciplinas**, abre uma disciplina e associa os professores que a podem lecionar.
5. Volta ao site e abre **Gerir sessões**.
6. Carrega em **Nova sessão**, escolhe disciplina, professor, data e uma hora da lista.
7. Guarda. O fim é calculado automaticamente após uma hora.
8. Consulta a sessão no plano semanal.

As contas de professor e administrador são criadas na área de gestão. O registo público cria apenas alunos. Para indicar a disponibilidade de um professor, entra com a conta desse professor na respetiva área.

Uma sessão com alunos inscritos não permite mudar o professor, disciplina ou horário nesta versão. Usa **Cancelar**, indicando o motivo, e cria outra sessão. Os participantes recebem um aviso no site. As sessões e inscrições são mantidas no histórico.

**Checkpoint:** consegues criar uma sessão que respeita a disciplina e a disponibilidade do professor.

## 9 Perceber as cores

| Ocupação | Cor | Significado |
| --- | --- | --- |
| 0/3 | Cinzento | Ainda sem alunos; pode receber inscrições |
| 1/3 | Verde | Mínimo atingido; duas vagas |
| 2/3 | Verde | Mínimo atingido; uma vaga |
| 3/3 | Vermelho | Completa; inscrições bloqueadas |
| Cancelada | Cinzento | Não aceita inscrições |

O texto acompanha a cor. As cores identificam a ocupação; o nome identifica a disciplina.

## 10 Confirmar a base de dados

Executa:

```sh
docker compose exec web python manage.py verificar_base_dados
```

Deves ver o motor `mysql`, as contagens dos registos e a confirmação de que nenhuma sessão tem mais de três alunos ativos.

Para consultar tabelas com SQL, abre o cliente MySQL:

```sh
docker compose exec db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u explica explica_facil'
```

O comando usa a configuração que já existe no contentor. Não precisas de copiar a palavra-passe. No PowerShell, mantém as aspas simples exteriores tal como estão.

Dentro do cliente, experimenta:

```sql
SHOW TABLES;
SELECT id, nome, ativa FROM explicacoes_disciplina;
SELECT id, inicio, fim, estado FROM explicacoes_sessao;
SELECT sessao_id, COUNT(*) AS alunos
FROM explicacoes_inscricao
WHERE estado = 'ativa'
GROUP BY sessao_id;
EXIT;
```

Não alteres manualmente inscrições ou sessões na base: isso contornaria as validações do site. Para aprender SQL, começa com consultas `SELECT`.

**Checkpoint:** consegues identificar uma sessão na página e na tabela da base de dados.

## 11 Experimentar os avisos

1. Entra como administrador.
2. Em **Gerir sessões**, escolhe uma sessão futura e carrega em **Avisar**.
3. Confirma os destinatários mostrados e escreve uma mensagem.
4. Envia o aviso.
5. Sai e entra como um aluno inscrito ou como o professor dessa sessão.
6. Abre **Avisos** e marca a mensagem como lida.

Esta versão guarda mensagens dentro do site. Não envia emails, SMS ou notificações push. O email pode ser acrescentado depois, quando o serviço de envio estiver definido.

## 12 Executar os testes

```sh
docker compose exec web python manage.py test --noinput
```

O Django cria uma base de dados separada para os testes e elimina-a no fim. A base das tuas demonstrações não é apagada. O resultado esperado é `OK`. Entre os testes estão as permissões, os cancelamentos, os conflitos e dois pedidos simultâneos para a última vaga.

Também podes executar:

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
```

O primeiro verifica a configuração. O segundo confirma que os modelos correspondem às migrações guardadas.

## 13 Aprender o código por esta ordem

Dedica uma pequena sessão a cada ponto. Experimenta no site antes de ler o ficheiro.

1. **HTML e CSS:** abre `templates/registration/login.html` e `static/css/style.css`. Identifica o título, o formulário e as cores.
2. **Endereços:** abre `explicacoes/urls.py`. Liga cada endereço à página que visitas.
3. **Dados:** abre `explicacoes/models.py`. Começa por `Disciplina`, depois `Sessao` e `Inscricao`.
4. **Formulários:** abre `explicacoes/forms.py`. Identifica os campos pedidos ao utilizador.
5. **Páginas em Python:** abre `explicacoes/views.py`. Procura a função `plano`.
6. **Regras:** abre `explicacoes/services.py`. Estuda primeiro `inscrever` e depois `cancelar_inscricao`.
7. **Testes:** abre `explicacoes/tests/test_inscricoes.py` e relaciona cada teste com uma regra.

Lê o `MAPA_DO_CODIGO.md` para acompanhar o percurso de um clique até à base de dados.

## 14 Fazer uma primeira alteração pequena

1. Abre `templates/registration/login.html`.
2. Procura o texto **Vamos aprender?**.
3. Troca por um texto teu, por exemplo **Bem-vindo ao Explica Fácil**.
4. Guarda o ficheiro.
5. Atualiza a página de entrada no navegador.

O ficheiro está partilhado com o contentor, por isso uma alteração a um template não exige reconstruir a imagem. Mantém as instruções entre `{% ... %}` e as variáveis entre `{{ ... }}` enquanto aprendes.

**Checkpoint:** consegues alterar um texto e ver a mudança.

## 15 Ajustar os horários fixos

Abre o `.env` e procura:

```text
SESSION_START_TIMES=09:00,10:00,11:00,14:00,15:00,16:00,17:00
ALLOWED_WEEKDAYS=0,1,2,3,4
```

Os dias são numerados de zero, segunda-feira, a seis, domingo. Estes são horários de exemplo, não horários já aprovados pelo professor.

Depois de alterar a configuração, recria o serviço web para carregar os novos valores:

```sh
docker compose up -d --force-recreate web
```

A alteração da lista não muda as sessões já guardadas. Escolhe o horário definitivo antes de começar a registar sessões reais de demonstração.

## 16 Parar e voltar a abrir

Para parar os serviços sem apagar os dados:

```sh
docker compose stop
```

Para voltar a iniciar:

```sh
docker compose start
```

Não precisas de repetir o comando de demonstração todos os dias. O volume `mysql_data` conserva os dados. Não uses `docker compose down -v`: essa opção apaga o volume da base de dados.

## 17 Resolver problemas comuns

**O Docker não está pronto:** abre o Docker Desktop e espera antes de repetir `iniciar.py`.

**O comando Python não existe:** tenta `py` no Windows ou `python3` no macOS/Linux. Se nenhum existir, instala Python 3.

**A porta 8008 está ocupada:** muda `HOST_PORT=8008` para uma porta livre, por exemplo `HOST_PORT=8018`, no `.env`. Executa `docker compose up -d` e abre a nova porta no navegador.

**A página não abre:** executa `docker compose ps` e `docker compose logs --tail=40 web`. Confirma também o estado do Docker.

**A sessão não aparece:** verifica a semana, os filtros e a data. A demonstração cria apenas sessões futuras.

**O professor está indisponível:** confirma a associação à disciplina e se o intervalo de disponibilidade cobre a hora inteira.

**O MySQL recusa a palavra-passe depois de mudares o `.env`:** as palavras-passe iniciais só são aplicadas quando o volume é criado. Não apagues o volume para resolver sem guardar os dados. Volta à configuração anterior e pede orientação para alterar a palavra-passe corretamente.

**Erros no teste de criação da base:** este projeto concede acesso apenas à base normal e à base de testes. Se reutilizares um volume antigo de outro projeto, essas permissões podem não existir. Este projeto deve usar o seu próprio volume.

## 18 O que guardar para o relatório

- Imagem do plano com sessões de várias ocupações.
- Imagem de uma inscrição confirmada e de uma quarta inscrição recusada.
- Imagem da disponibilidade do professor e dos alunos da sua sessão.
- Imagem da área de gestão de disciplinas e professores.
- Imagem de um cancelamento e do aviso correspondente.
- Resultado dos testes executados com MySQL.
- Explicação da função de cada pasta e de uma regra que saibas apresentar.

Usa contas fictícias nas imagens. O código, as imagens e os resultados devem corresponder à versão que vais apresentar.

## 19 Partilhar o projeto

Entrega o código e a documentação no repositório pedido pelo formador. O `.gitignore` já exclui o `.env`, caches e ficheiros locais. Os dados da demonstração podem ser recriados com `preparar_demo`.

Não publiques este ambiente de aprendizagem diretamente na internet: está configurado para desenvolvimento local. A publicação será uma etapa própria, com configuração adequada e contas de demonstração revistas.

## 20 Guardar uma cópia e testar o restauro

Depois de terminares os testes automáticos, executa no Windows:

```sh
py backup.py
```

No macOS/Linux:

```sh
python3 backup.py
```

O comando apresenta o nome de uma cópia SQL dentro de `backups`. Para testar que essa cópia pode ser lida, usa o nome real do ficheiro apresentado:

```sh
python3 verificar_restauro.py backups/NOME_REAL_DO_FICHEIRO.sql
```

No Windows, troca `python3` por `py`. O teste substitui apenas a base temporária `test_explica_facil`, importa a cópia, mostra contagens e remove a base temporária no fim. Não o executes ao mesmo tempo que `manage.py test`, que usa o mesmo nome de base de testes. A base normal `explica_facil` mantém-se intacta.

Os ficheiros de cópia contêm os dados da aplicação e ficam excluídos do repositório. Não é necessário incluí-los na entrega do código; os dados fictícios podem ser recriados pelo comando de demonstração.
