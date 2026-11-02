# Verificação desta versão

Validação realizada em 26 de outubro de 2026.

## Verificações concluídas

| Verificação | Resultado |
| --- | --- |
| Arranque no Docker com Django e MySQL 8.4 | Concluído |
| Página de entrada por HTTP | Resposta 200 |
| Verificação de configuração do Django | Sem problemas identificados |
| Correspondência entre modelos e migrações | Sem alterações pendentes |
| Testes automáticos com MySQL | 44 testes aprovados, sem testes ignorados |
| Dois alunos a disputar a última vaga | Só uma inscrição aceite |
| Mesmo aluno em pedidos simultâneos sobrepostos | Só uma inscrição aceite |
| Repetição do comando de demonstração | Zero sessões duplicadas |
| Reinício dos serviços | Dados mantidos |
| Cópia SQL e restauro numa base temporária | 18 sessões e 25 inscrições restauradas |

Os dados de demonstração usados na verificação tinham oito utilizadores, três disciplinas, quinze intervalos de disponibilidade, dezoito sessões e vinte e cinco inscrições. As contagens mudam quando se experimenta o site.

## Limites da verificação

A inspeção visual do site no navegador não foi concluída porque o controlo do navegador não tinha permissões. As páginas foram verificadas pelos testes Django e por HTTP. A revisão visual em computador e telemóvel deve ser feita com o guia antes da apresentação.

Não foi configurado envio de email ou publicação online. As notificações implementadas são internas ao site. Os horários e dias incluídos são exemplos configuráveis, a validar com o formador.

## Voltar a verificar

```sh
docker compose exec web python manage.py test --noinput
docker compose exec web python manage.py verificar_base_dados
docker compose exec web python manage.py makemigrations --check --dry-run
```
