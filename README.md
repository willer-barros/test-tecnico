# TESTE TECNICO

## SECTION A
**Tempo de realização:** 12 minutos

### A1
- Validações básicas no front com required nos campos (nome, email ou telefone, consentimento marcado).
Desabilitar botão de envio enquanto o form está sendo enviado.

- Método POST com CSRF, schema validado e normalizado com as funções trim para limpar caracteres indesejados, check-box explícito com true salvo com `current_timestamp`.

- Tratamento de erro 422 com botão de reenvio caso aconteça esse erro mantendo as informações preenchidas pelo cliente no form.

- Gerar o `idempotencia-key` por tentativa e reutilização no retry.

### A2
- Cookies
- Cors

### A3
- Para casos de mudança de privilégios, gerar um novo ID de sessão e invalidar o antigo.
- Logout no lado do usuário e timeout por inatividade.
- JWT para autenticação.

### A4
```sql
SELECT id, subject, received_at
FROM messages
WHERE tenant_id = :current_tenant_id
ORDER BY received_at DESC, id DESC
LIMIT 25;
```

---

## SECTION B
**Tempo de realização:** 15 minutos

### Nas linhas 5, 8, 11 e 14
- **Risk:** Não tem validação do tenant
- **Fix:** Filtrar pelo `tenant_id`
- **Negative test:** Lead do T-A precisa especificar outro agent

---

### Nas linhas 7, 8 e 11
- **Risk:** SQL Injection
- **Fix:** Validar id como inteiro
- **Negative test:** Erro de escrita no status = `"x"`

---

### Nas linhas 6, 9
- **Risk:** Mudança de estado via GET: com cookie de sessão, um `<img src="/lead.php?id=1&status=...">` em outro site altera dados (CSRF); também aparece em logs e cache;
- **Fix:** Mudar estado só com POST/PATCH + token CSRF; usar GET apenas para leitura
- **Negative test:** GET não altera estado.

---

### Nas linhas 6, 9
- **Risk:** Qualquer valor é aceito
- **Fix:** O `WHERE status='contact_lawyer'` no UPDATE; estados finais são terminais
- **Negative test:** Lead sendo mudado

---

## SECTION C
**Tempo de realização:** 15 minutos  
**Link do repositório:** https://github.com/willer-barros/test-tecnico

---

## SECTION D
**Tempo de realização:** 15 minutos

### D. Plano de teste de segurança (staging autorizado)

#### D1. Escopo e evidência
- **Antes de testar:** Autorização escrita do dono do sistema; hosts/URLs de staging em escopo e produção fora; janela de horário; técnicas permitidas (sem DoS, sem engenharia social, sem provedores de terceiros reais); limites de taxa; contatos de emergência.
- **Contas e dados:** Dois tenants fictícios, contas de agent A, agent B e manager, só dados sintéticos.
- **Condições de parada:** Aparecer dado real ou PII, credencial de pessoa real, degradação do serviço, sistema fora do escopo, sinais de produção. Em qualquer uma, paro e aviso.
- **Relatório:** Título, severidade com justificativa, componente, pré-condições, passos de reprodução com contas fictícias, esperado × obtido, evidência, impacto, correção sugerida, passos de reteste.
- **Evidência segura:** Nada de dado real; mascarar cookies, tokens, Authorization e IDs; recortar capturas; limpar logs; guardar evidências com acesso restrito e prazo de retenção.

#### D2. Download de PDF privado
- **Preparação:** Tenant A tem lead LA com PDF PA (hash SHA-256 conhecido); Tenant B tem LB com PB.
- **Download autorizado:** O agent do tenant A pede o PA. Espero 200, `Content-Type: application/pdf`, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `Cache-Control: private/no-store`, hash dos bytes igual ao do PA e entrada no log de auditoria.
- **Negação cross-tenant:** A mesma conta pede o PB (também testo o ID do PB dentro do caminho do LA). Espero 404 (ou 403, conforme a política), sem corpo, sem nome de arquivo ou metadado, resposta idêntica à de um documento inexistente, e a negação registrada. Também testo sem login, esperando 401.
- **Duas proteções a inspecionar:** No upload, validação por magic bytes, limite de tamanho, nome aleatório fora do web root (evita path traversal) e varredura de malware; no download, URL assinada de vida curta atrelada a usuário e tenant, e nome de arquivo sanitizado.

#### D3. Lembretes e duplicatas (relógio falso + provedor mock que apenas registra envios)
- **Lembrete agendado para t0+48h:** Aos 47h59 espero 0 envios; aos 48h, exatamente 1 envio ao destinatário fictício.
- **Cancelamento:** Tiro o lead de `contact_lawyer` antes das 48h. O worker deve rechecar o estado na hora da execução, não só no agendamento. Espero 0 envios e o job marcado como cancelado. Também testo a mudança de estado no instante do vencimento.
- **Duplicata/retry:** Entrego o mesmo job duas vezes e simulo o worker caindo depois de chamar o provedor. A defesa é a reivindicação atômica (`UPDATE ... SET status='sending' WHERE id=? AND status='pending'`) mais chave de idempotência por `reminder_id`. Assert: o mock recebeu exatamente 1 chamada e o status final é `sent`.
- Simulo timeout do provedor e confirmo que o retry não duplica o envio.

---

## SECTION E
**Tempo de realização:** 3 minutos

### E. IA e segurança de documentos
- **Por que é perigoso:** Eu sabia que texto em PDF é perigoso, porém não sei o motivo. Profissionalmente nunca resolvi situação parecida.

---

## SECTION F
**Tempo de realização:** 3 minutos

I found that any logged-in staff member could open or change any lead, including other companies' leads, just by changing the ID in the request. This could expose private client information and let someone alter funding decisions, which is a serious business and legal risk. My fix checks the user's company and role on the server for every update, and only the assigned agent or a manager of the same company can change a lead. I wrote and ran 9 automated tests on fictional data, and they all pass. I only tested a small local function, not a real database, a live system or production, so concurrent updates and the HTTP layer still need to be verified before release.

---

## Ferramentas de Desenvolvimento
- VSCode
- Python 3.13
- Claude para debug nos testes

**Tempo Total:** 63 minutos
