def navigation(request):
    total = request.user.notificacoes.filter(lida_em__isnull=True).count() if request.user.is_authenticated else 0
    return {"notificacoes_por_ler": total}
